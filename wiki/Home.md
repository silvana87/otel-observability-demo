# Observabilidad con OpenTelemetry — de la teoría a un demo que puedes correr

Esta wiki acompaña al repositorio. Nació como material de una capacitación
interna sobre observabilidad y OpenTelemetry, y se adaptó para que cualquier
persona o equipo pueda usarla — no asume ninguna empresa, nube o stack en
particular, aunque el demo de código está armado sobre un caso muy común:
un servicio serverless orientado a eventos (piensa en una función de
extracción de datos que dispara a otra función de procesamiento).

Si vienes de la charla / capacitación, puedes saltar directo a la sección
que te interese. Si llegaste por tu cuenta buscando entender observabilidad
y OpenTelemetry desde cero, te recomendamos seguir el orden de abajo.

## Índice

1. **[[01 Monitoreo vs Observabilidad]]** — qué problema resuelve cada uno, y cuándo necesitas el segundo.
2. **[[02 Fundamentos de OpenTelemetry]]** — qué es, sus 3 señales, y las piezas del ecosistema (SDK, API, Collector, exporters).
3. **[[03 Arquitectura del Stack Grafana]]** — qué es Grafana, Tempo, Loki, Prometheus, y cómo encajan entre sí (y con OTel).
4. **[[04 Guia de Instalacion]]** — cómo levantar el demo en tu máquina, paso a paso, con solución de problemas comunes.
5. **[[05 Explicacion del Codigo]]** — arquitectura del demo, flujo completo, qué hace cada archivo.
6. **[[06 Propagacion de Contexto en Mensajeria]]** — cómo se propaga una traza cuando en vez de una llamada HTTP directa hay una cola/tópico de mensajería en el medio (Pub/Sub, SQS, RabbitMQ, Kafka...).
7. **[[07 Integrar Otros Backends]]** — cómo apuntar este mismo demo a Jaeger, Grafana Cloud, Honeycomb, Datadog, New Relic, Google Cloud Trace, AWS X-Ray, o cualquier otro backend compatible con OTLP.
8. **[[08 Adaptar a tu Stack]]** — cómo llevar este mismo patrón a otros lenguajes (Node.js, Java, Go, .NET) y otros entornos de cómputo (AWS Lambda, contenedores en Kubernetes, VMs).
9. **[[09 Preguntas Frecuentes]]** — respuestas cortas a las dudas que más salen al presentar esto en un equipo.

## Qué vas a poder demostrar con este repo

Al final de la [[04 Guia de Instalacion|guía de instalación]] vas a tener,
corriendo en tu propia laptop, un pipeline de dos servicios instrumentado
con OpenTelemetry, visualizando una **traza distribuida real** en Grafana:

```
Servicio A (extracción)
├── operación interna A.1        (ej. consulta a una base de datos)
└── operación interna A.2
    └── llamada a Servicio B     (con el contexto de traza propagado
        └── Servicio B            automáticamente en el header HTTP)
            └── operación interna B.1
```

Todo corre local, sin necesidad de cuenta en ningún proveedor cloud.

## Requisitos

- Docker y Docker Compose (Docker Desktop en Mac/Windows, o Docker Engine + plugin compose en Linux)
- Un poco de Python si quieres modificar el código de los servicios de ejemplo (no es necesario para solo correr el demo)

## Licencia

MIT — usa, adapta y comparte este material libremente, dando crédito si te
sirvió. Ver [LICENSE](../LICENSE).
