# Observabilidad con OpenTelemetry — demo + material de capacitación

Un demo funcional, corriendo 100% en local con Docker, que muestra
**observabilidad de extremo a extremo con OpenTelemetry**: dos servicios
instrumentados, una traza distribuida real, visualizada en Grafana. Pensado
como material de capacitación — no asume ninguna nube, empresa ni stack en
particular, aunque el ejemplo de código está armado sobre un patrón muy
común: un servicio serverless orientado a eventos (una función que extrae
datos y dispara a otra que los procesa).

Incluye también una wiki completa con la teoría (monitoreo vs
observabilidad, fundamentos de OpenTelemetry, cómo integrar otros backends,
cómo adaptar el patrón a otros lenguajes) y las preguntas que más salen al
presentar esto en un equipo.

## Qué vas a ver corriendo

```
Servicio A (extracción)
├── operación interna A.1        (ej. consulta a una base de datos)
└── operación interna A.2
    └── llamada a Servicio B     (con el contexto de traza propagado
        └── Servicio B            automáticamente, sin código extra)
            └── operación interna B.1
```

Una sola traza, dos servicios, spans anidados con duraciones reales —
visualizada en Grafana Tempo, corriendo en tu laptop, sin cuenta en ningún
proveedor cloud.

## Quick start

Requisitos: Docker y Docker Compose, con el daemon corriendo.

```bash
git clone <url-de-este-repo>
cd <nombre-del-repo>
docker compose up --build
```

En otra terminal:

```bash
chmod +x trigger.sh
./trigger.sh 3
```

Abre **http://localhost:3000** → Explore → datasource **Tempo** → busca
`Service Name = cf1-extraccion-bigquery`.

Guía completa, con solución de problemas comunes, en
[wiki/04-Guia-de-Instalacion.md](wiki/04-Guia-de-Instalacion.md).

## Estructura del repo

```
.
├── cf1/                              # Servicio A: simula extracción de datos
├── cf2/                              # Servicio B: simula procesamiento
├── docker-compose.yml                # Stack principal (Tempo + Grafana)
├── docker-compose.jaeger.yml         # Stack alternativo (Jaeger en vez de Tempo/Grafana)
├── otel-collector-config.yaml        # Config del Collector -> Tempo
├── configs/
│   ├── otel-collector-jaeger.yaml    # Config del Collector -> Jaeger
│   └── otel-collector-vendors.yaml.example  # Plantilla: Grafana Cloud, Honeycomb, Datadog, New Relic...
├── tempo.yaml                        # Config mínima de Tempo
├── grafana/provisioning/             # Grafana arranca con Tempo ya configurado
├── trigger.sh                        # Dispara el pipeline N veces
└── wiki/                             # Contenido teórico completo (ver abajo)
```

## Material de capacitación (wiki)

La carpeta [`wiki/`](wiki/) contiene todo el contenido teórico, en el mismo
formato que usa la Wiki nativa de GitHub.

Índice de contenido:

1. [Monitoreo vs Observabilidad](wiki/01-Monitoreo-vs-Observabilidad.md)
2. [Fundamentos de OpenTelemetry](wiki/02-Fundamentos-de-OpenTelemetry.md)
3. [Arquitectura del Stack Grafana](wiki/03-Arquitectura-del-Stack-Grafana.md)
4. [Guía de Instalación](wiki/04-Guia-de-Instalacion.md)
5. [Explicación del Código](wiki/05-Explicacion-del-Codigo.md)
6. [Propagación de Contexto en Mensajería](wiki/06-Propagacion-de-Contexto-en-Mensajeria.md)
7. [Integrar Otros Backends](wiki/07-Integrar-Otros-Backends.md)
8. [Adaptar a tu Stack](wiki/08-Adaptar-a-tu-Stack.md)
9. [Preguntas Frecuentes](wiki/09-Preguntas-Frecuentes.md)

## Probar con otros backends

Este repo no ata la instrumentación a Grafana/Tempo — es solo el backend
por defecto porque no requiere credenciales. Para probar con Jaeger:

```bash
docker compose -f docker-compose.jaeger.yml up --build
./trigger.sh 3
# UI: http://localhost:16686
```

Para Grafana Cloud, Honeycomb, Datadog, New Relic, Google Cloud Trace, AWS
X-Ray, Zipkin o SigNoz, ver la plantilla documentada en
[`configs/otel-collector-vendors.yaml.example`](configs/otel-collector-vendors.yaml.example)
y la guía en
[wiki/07-Integrar-Otros-Backends.md](wiki/07-Integrar-Otros-Backends.md).

## Adaptar a tu propio stack

El código de ejemplo es Python + Flask, pero el patrón (instrumentación
automática + spans manuales + propagación de contexto + Collector
transversal) es igual en cualquier lenguaje. Ver
[wiki/08-Adaptar-a-tu-Stack.md](wiki/08-Adaptar-a-tu-Stack.md) para
ejemplos en Node.js, Java, Go, .NET, y para entornos serverless/Kubernetes.

## Contribuir

Si encuentras un error, tienes un caso de uso que valdría la pena agregar
(otro backend, otro lenguaje), o quieres mejorar alguna explicación, los
issues y pull requests son bienvenidos.

## Licencia

[MIT](LICENSE) — usa, adapta y comparte este material libremente.
