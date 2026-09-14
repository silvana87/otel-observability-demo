# Fundamentos de OpenTelemetry

## Qué es

OpenTelemetry (a menudo abreviado **OTel**) es un proyecto de la
[CNCF](https://www.cncf.io/) — el mismo hogar de Kubernetes y Prometheus —
que define un **estándar abierto y vendor-neutral** para instrumentar,
generar, recolectar y exportar datos de telemetría (trazas, métricas,
logs).

Un matiz importante: **OpenTelemetry no es una herramienta de
visualización ni un backend de almacenamiento**. No tiene una interfaz
donde tú "veas" tus trazas — es la capa de **instrumentación y transporte**.
Lo que tú ves en pantalla (Grafana, Jaeger, Datadog, lo que sea) es un
producto aparte que consume los datos que OTel produjo. Ver
[[03 Arquitectura del Stack Grafana]] para el ejemplo concreto de esta
separación.

## Las 3 señales unificadas

| Señal | Qué representa |
|---|---|
| **Traces** (trazas) | El recorrido completo de una operación a través de uno o varios servicios, dividido en *spans* (ver abajo) |
| **Metrics** (métricas) | Valores numéricos agregados: latencia, tasa de error, throughput |
| **Logs** | Eventos discretos con contexto — correlacionados automáticamente con la traza activa cuando corresponde |

Antes de OTel, cada una de estas señales solía tener su propio SDK, su
propio formato, y muchas veces su propio vendor. OTel las unifica bajo un
único modelo de datos y un único protocolo de transporte (**OTLP** —
OpenTelemetry Protocol).

## Qué es un span

Un **span** es la unidad mínima de una traza: representa una operación con
inicio y fin — "esto empezó en el tiempo X y terminó en el tiempo Y". Una
traza completa no es más que un árbol de spans conectados entre sí.

Cada span contiene:

- **Un nombre** (ej. `"consulta-base-de-datos"`)
- **Un `trace_id`** — identifica a qué traza pertenece (el mismo en todos
  los spans de una misma operación de punta a punta)
- **Un `span_id`** propio — único, identifica a este span en particular
- **Un `parent_span_id`** — de qué span "cuelga" (de ahí sale la jerarquía
  anidada que ves en un waterfall)
- **Timestamps de inicio y fin** → de ahí sale la duración
- **Atributos** — pares clave-valor que agregas a mano para dar contexto
  de negocio (ej. `filas_procesadas: 18342`)
- **Un status** (ok / error) y, opcionalmente, eventos o excepciones
  registrados dentro del span

### Cómo se arma la jerarquía padre-hijo

En la API de OTel, esto normalmente se ve así (ejemplo en Python, pero el
concepto es igual en cualquier lenguaje):

```python
with tracer.start_as_current_span("A"):
    # A queda "activo"
    with tracer.start_as_current_span("B"):
        # B se abre mientras A sigue activo -> B queda como HIJO de A,
        # automáticamente, sin que tengas que pasar ningún ID a mano.
        ...
    # al salir de este bloque, B se cierra (se calcula su duración)
# al salir de este bloque, A se cierra
```

### Spans automáticos vs manuales

- **Automáticos**: generados por librerías de auto-instrumentación (por
  ejemplo, una que engancha tu framework web y crea un span por cada
  request entrante, o una que engancha tu cliente HTTP y crea un span por
  cada llamada saliente). No escribes código para que existan.
- **Manuales**: los abres tú explícitamente para marcar trabajo interno
  específico que te importa medir (una consulta a una base de datos, una
  transformación de datos, una llamada a un servicio externo sin
  instrumentación disponible).

## Instrumentación: API vs SDK

- La **API** de OTel es la interfaz que usas en tu código para crear spans,
  métricas y logs (`tracer.start_as_current_span(...)`, etc.). Es estable
  y minimalista a propósito.
- El **SDK** es la implementación real detrás de esa API: decide cómo se
  procesan los spans (en lote o uno por uno), a dónde se exportan, con qué
  muestreo, etc. Se configura una sola vez, al arrancar la aplicación.

Esta separación es intencional: tu código de negocio usa la API (estable,
no cambia), y la configuración del SDK (que sí puede cambiar — de exportar
a un backend a otro, por ejemplo) vive en un solo lugar, típicamente el
punto de entrada de tu aplicación.

## El Collector

El **OTel Collector** es un proceso separado (no una librería que
importas, sino un servicio que corre aparte) que recibe telemetría de tus
aplicaciones, opcionalmente la procesa (filtra, agrega atributos, muestrea)
y la reenvía a uno o varios backends.

Es, en la práctica, el "enchufe universal": tus servicios exportan siempre
de la misma forma (OTLP, al Collector), y **cambiar de backend es un
cambio de configuración del Collector, no un cambio de código en cada
servicio**. Ver [[07 Integrar Otros Backends]] para ejemplos concretos.

El Collector no es obligatorio (tus servicios pueden exportar directo a un
backend que hable OTLP), pero es la pieza recomendada en cualquier
arquitectura con más de un servicio, porque:

- Centraliza configuración de destino, credenciales y políticas de
  muestreo — no las repites en cada servicio.
- Te permite cambiar de backend, o exportar a varios a la vez, sin tocar
  ni redeployar tus aplicaciones.
- Puede aplicar procesamiento común (batching, filtrado de datos
  sensibles, enriquecimiento) en un solo lugar.

## Propagación de contexto

Cuando el Servicio A llama al Servicio B, ¿cómo sabe B que debe continuar
la misma traza de A en vez de empezar una propia? Viajando un pequeño
paquete de datos — el **contexto de traza** — junto con la llamada.

El formato estándar (W3C Trace Context) se ve así, viajando típicamente en
un header HTTP llamado `traceparent`:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             │  └────────── trace_id ──────────┘ └── span_id ──┘  │
           versión                                             flags
```

Cuando la comunicación es HTTP directa, las librerías de
auto-instrumentación suelen inyectar y leer este header sin que tengas que
hacer nada. Cuando en el medio hay una cola de mensajería (Pub/Sub, SQS,
RabbitMQ, Kafka...), no hay header HTTP que instrumentar automáticamente —
tienes que propagar el contexto a mano. Ver
[[06 Propagacion de Contexto en Mensajeria]] para el patrón completo, con
código.

## Siguiente paso

Con estos conceptos claros, [[03 Arquitectura del Stack Grafana]] explica
dónde termina yendo toda esta telemetría en el demo de este repo.
