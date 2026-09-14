# Adaptar a tu Stack

Este demo usa Python + Flask + contenedores locales porque es rápido de
levantar y fácil de leer, pero el patrón —instrumentación automática +
spans manuales + propagación de contexto + exportación a un Collector— es
igual en cualquier lenguaje y cualquier entorno de cómputo. Esta página da
el punto de partida para adaptarlo a lo que uses en tu equipo.

## Node.js / TypeScript (Express, NestJS)

```bash
npm install @opentelemetry/api @opentelemetry/sdk-node \
  @opentelemetry/exporter-trace-otlp-grpc \
  @opentelemetry/instrumentation-http \
  @opentelemetry/instrumentation-express  # o el paquete de NestJS/Fastify que uses
```

```javascript
// tracing.js — se importa ANTES que cualquier otro módulo de tu app
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'mi-servicio-nestjs',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4317',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

Un span manual se ve así:

```javascript
const { trace } = require('@opentelemetry/api');
const tracer = trace.getTracer('mi-servicio');

async function procesarPedido(pedido) {
  return tracer.startActiveSpan('procesar-pedido', async (span) => {
    span.setAttribute('pedido.id', pedido.id);
    try {
      // ... lógica ...
    } finally {
      span.end();
    }
  });
}
```

`getNodeAutoInstrumentations()` ya cubre Express, NestJS (vía Express/
Fastify por debajo), `http`/`https`, y clientes de bases de datos comunes
— la propagación de contexto en llamadas HTTP salientes funciona igual de
automática que en el demo de Python.

## Java (Spring Boot y otros)

Java tiene la opción más simple de todas: el **Java agent** de OTel se
adjunta al arrancar la JVM, sin tocar código:

```bash
java -javaagent:opentelemetry-javaagent.jar \
     -Dotel.service.name=mi-servicio-java \
     -Dotel.exporter.otlp.endpoint=http://localhost:4317 \
     -jar mi-app.jar
```

Esto instrumenta automáticamente frameworks web (Spring, Micronaut,
Quarkus...), clientes HTTP, drivers de base de datos, y más — sin cambios
de código. Para spans manuales, se usa la misma API estándar de OTel,
inyectando un `Tracer` vía el SDK de Java.

## Go

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/trace"
)

exporter, _ := otlptracegrpc.New(ctx, otlptracegrpc.WithEndpoint("localhost:4317"), otlptracegrpc.WithInsecure())
tp := trace.NewTracerProvider(trace.WithBatcher(exporter))
otel.SetTracerProvider(tp)

tracer := otel.Tracer("mi-servicio-go")
ctx, span := tracer.Start(ctx, "procesar-pedido")
defer span.End()
```

## .NET

```csharp
services.AddOpenTelemetry()
    .WithTracing(builder => builder
        .SetResourceBuilder(ResourceBuilder.CreateDefault().AddService("mi-servicio-dotnet"))
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter(o => o.Endpoint = new Uri("http://localhost:4317")));
```

## Otros entornos de cómputo

El demo usa Flask en contenedores locales para simplificar, pero el mismo
patrón de instrumentación aplica a:

### AWS Lambda / Azure Functions / Google Cloud Functions

La instrumentación del código es igual (SDK de OTel del lenguaje que
uses). Lo que cambia es:

- **El exporter suele usar batching más agresivo o modo síncrono**, porque
  la ejecución puede terminar (y el proceso congelarse/destruirse) antes de
  que el `BatchSpanProcessor` alcance a enviar el lote — en funciones muy
  cortas conviene forzar un `flush` explícito al final del handler, o usar
  extensiones específicas (por ejemplo, la
  [capa Lambda de OTel](https://github.com/open-telemetry/opentelemetry-lambda) para AWS).
- **La propagación entre funciones casi siempre pasa por mensajería**
  (Pub/Sub, SQS, EventBridge...), no por HTTP directo — ver
  [[06 Propagacion de Contexto en Mensajeria]].

### Kubernetes / GKE / EKS

Dos formas de instrumentar, no excluyentes:

- **A nivel de aplicación** (lo que ve este demo): el SDK de OTel dentro de
  cada pod, exportando al Collector — funciona igual que en contenedores
  locales, solo cambia el `OTEL_EXPORTER_OTLP_ENDPOINT` a la URL interna
  del Collector dentro del clúster (normalmente desplegado como
  DaemonSet o Deployment).
- **A nivel de infraestructura/mesh** (ej. Istio): un sidecar captura
  automáticamente los saltos de red entre pods, sin tocar código. Es
  complementario a la instrumentación de aplicación, no un sustituto —
  el mesh ve "hubo una llamada de A a B y tardó X", pero no ve qué pasó
  *dentro* de A (una consulta a base de datos, una transformación
  interna) a menos que también instrumentes la aplicación.

### VMs / bare metal

Igual que local: el SDK corre dentro del proceso de tu aplicación, y
exporta al Collector por red (puede ser el mismo host, otra VM, o un
servicio gestionado).

## El principio que no cambia

Sin importar el lenguaje ni el entorno, la arquitectura conceptual es
siempre la misma que la de este repo:

```
tu código (SDK de OTel del lenguaje que uses)
        │
        ▼  OTLP
  OTel Collector          <- transversal, uno para todos tus servicios
        │
        ▼
   backend elegido        <- transversal, el mismo para toda la empresa/equipo
```

## Siguiente paso

[[09 Preguntas Frecuentes]] recopila las dudas más comunes que suelen salir
al presentar este material a un equipo.
