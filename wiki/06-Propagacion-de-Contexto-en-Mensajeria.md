# Propagación de Contexto en Mensajería

El demo de este repo usa HTTP directo entre `cf1` y `cf2`, donde las
librerías de auto-instrumentación (`RequestsInstrumentor`,
`FlaskInstrumentor`) inyectan y leen el header `traceparent` sin que
tengas que escribir nada. Pero muchas arquitecturas reales — sobre todo
serverless orientadas a eventos — conectan sus servicios a través de una
**cola o tópico de mensajería**: Google Pub/Sub, AWS SQS/SNS, RabbitMQ,
Kafka, Azure Service Bus, etc.

## Por qué esto es distinto

La auto-instrumentación HTTP funciona porque hay un lugar estándar y
conocido donde meter datos extra: los **headers** de la request/response.
Los sistemas de mensajería no tienen ese concepto de forma automática —
el contexto de traza tiene que viajar dentro de los **atributos o
metadata del mensaje**, y ahí no existe una librería genérica que lo haga
sola para cualquier combinación de productor/consumidor. Tienes que
inyectarlo y extraerlo tú mismo, con dos funciones de la API de OTel:
`inject()` y `extract()`.

Esto aplica igual sin importar el proveedor — el patrón es el mismo,
solo cambia el nombre del SDK del mensajero.

## El patrón general

### Lado publicador

```python
from opentelemetry import propagate
from opentelemetry.trace import SpanKind

def publicar_evento(datos, publicar_mensaje_fn):
    with tracer.start_as_current_span("publish-message", kind=SpanKind.PRODUCER) as span:
        # 1) OTel escribe el trace_id + span_id actuales en un diccionario
        #    ("carrier"), en formato W3C Trace Context:
        #    {'traceparent': '00-<trace_id>-<span_id>-01'}
        carrier = {}
        propagate.inject(carrier)

        # 2) Ese carrier se manda junto con el mensaje, como metadata/
        #    atributos (el mecanismo exacto depende del proveedor — ver
        #    ejemplos abajo).
        span.set_attribute("messaging.system", "<tu-proveedor>")
        span.set_attribute("messaging.destination", "<tu-topico-o-cola>")
        publicar_mensaje_fn(datos, attributes=carrier)
```

### Lado receptor

```python
from opentelemetry import propagate
from opentelemetry.trace import SpanKind

def procesar_mensaje(mensaje):
    attributes = mensaje.get("attributes", {})  # aquí llega el traceparent

    # 1) Reconstruimos el contexto de traza a partir de esos atributos
    #    (el inverso exacto de propagate.inject)
    ctx = propagate.extract(attributes)

    # 2) Abrimos el span pasándole ese contexto EXPLÍCITAMENTE.
    #    Sin esto, el framework que invoca tu función (por ejemplo,
    #    functions-framework o un handler de Lambda) crearía una traza
    #    NUEVA, porque a nivel HTTP/invocación no hay ningún traceparent
    #    — el que importa está enterrado en el body/metadata del evento.
    with tracer.start_as_current_span("process-message", context=ctx, kind=SpanKind.CONSUMER) as span:
        span.set_attribute("messaging.system", "<tu-proveedor>")
        # ... procesar el payload del mensaje ...
```

**El punto que hay que recordar:** cualquier auto-instrumentación de
framework web (Flask, Express, etc.) en el servicio consumidor **no
sirve para esto** — va a crear su propio span basado en el request HTTP
que la infraestructura de mensajería usa internamente para invocar tu
función, pero ese request no tiene ninguna relación con el `trace_id`
del publicador. Por eso el `context=ctx` explícito es obligatorio.

## Ejemplos por proveedor

### Google Cloud Pub/Sub

```python
# Publicador
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, "mi-topico")

carrier = {}
propagate.inject(carrier)
future = publisher.publish(topic_path, data=payload_bytes, **carrier)
```

```python
# Receptor (Cloud Function disparada por Eventarc/Pub/Sub)
import functions_framework

@functions_framework.cloud_event
def entry_point(cloud_event):
    message = cloud_event.data["message"]
    ctx = propagate.extract(message.get("attributes", {}))
    with tracer.start_as_current_span("process", context=ctx):
        ...
```

### AWS SQS

```python
# Publicador
carrier = {}
propagate.inject(carrier)
sqs_client.send_message(
    QueueUrl=queue_url,
    MessageBody=payload_json,
    MessageAttributes={
        k: {"DataType": "String", "StringValue": v} for k, v in carrier.items()
    },
)
```

```python
# Receptor (handler de Lambda)
def lambda_handler(event, context):
    for record in event["Records"]:
        attrs = record.get("messageAttributes", {})
        carrier = {k: v["stringValue"] for k, v in attrs.items()}
        ctx = propagate.extract(carrier)
        with tracer.start_as_current_span("process", context=ctx):
            ...
```

### RabbitMQ

```python
# Publicador
carrier = {}
propagate.inject(carrier)
channel.basic_publish(
    exchange="mi-exchange",
    routing_key="mi-cola",
    body=payload_bytes,
    properties=pika.BasicProperties(headers=carrier),
)
```

```python
# Receptor
def callback(ch, method, properties, body):
    carrier = properties.headers or {}
    ctx = propagate.extract(carrier)
    with tracer.start_as_current_span("process", context=ctx):
        ...
```

### Kafka

Igual que RabbitMQ conceptualmente: el `carrier` se manda como headers
del mensaje de Kafka (`producer.send(topic, value=payload, headers=[(k, v.encode()) for k, v in carrier.items()])`), y se lee del lado
consumidor con `propagate.extract(...)` sobre esos mismos headers
decodificados.

## Siguiente paso

Ya viste cómo cambia la instrumentación según el medio de transporte.
[[07 Integrar Otros Backends]] cubre el otro eje de flexibilidad: a
dónde terminan yendo esos spans, sin importar cómo se propagaron.
