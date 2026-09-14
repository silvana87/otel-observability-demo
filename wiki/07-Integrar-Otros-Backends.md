# Integrar Otros Backends

Uno de los puntos centrales de usar OpenTelemetry es que **el código de tus
servicios nunca sabe a dónde terminan yendo sus spans** — solo sabe que
exportan por OTLP a `OTEL_EXPORTER_OTLP_ENDPOINT`. Cambiar de backend es,
en el caso más simple, cambiar esa variable de entorno; en el caso más
completo, es cambiar la configuración del Collector. En ningún caso se
toca `cf1/app.py` ni `cf2/app.py`.

Este repo incluye un ejemplo funcional adicional (Jaeger) y una plantilla
documentada para varios backends SaaS más.

## Nivel 1 — Otro backend self-hosted: Jaeger

[Jaeger](https://www.jaegertracing.io/) es otro backend de trazas open
source, alternativa a Tempo, con su propia UI incluida (no necesita
Grafana). Este repo trae un stack alternativo completo:

```bash
docker compose -f docker-compose.jaeger.yml up --build
./trigger.sh 3
```

Abre **http://localhost:16686** (la UI nativa de Jaeger) y busca el
servicio `cf1-extraccion-bigquery`.

Compara `configs/otel-collector-jaeger.yaml` contra
`otel-collector-config.yaml` (el que usa Tempo) — vas a ver que el bloque
`receivers` es **idéntico**; solo cambia `exporters`. Esa es la prueba en
código de "instrumentas una vez, cambias de backend sin tocar la
aplicación".

## Nivel 2 — Backends SaaS (Grafana Cloud, Honeycomb, Datadog, New Relic...)

El archivo `configs/otel-collector-vendors.yaml.example` trae bloques de
`exporters` listos para copiar y pegar para:

- **Grafana Cloud** (managed, en vez de tu propio Tempo)
- **Honeycomb**
- **New Relic**
- **Datadog**
- **Google Cloud Trace**
- **AWS X-Ray**
- **Zipkin** (otro backend open source, más liviano que Jaeger)
- **SigNoz** (backend open source todo-en-uno, alternativa self-hosted a Grafana Cloud)

Para usar cualquiera de estos:

1. Copia el bloque `exporters` que te interese a tu propio
   `otel-collector-config.yaml` (o crea uno nuevo, como se hizo con
   Jaeger).
2. Agrégalo a la lista de `exporters` del pipeline en `service.pipelines.traces`.
3. Define las credenciales como variables de entorno (nunca las escribas
   directo en el YAML si vas a subir el archivo a un repo) y pásalas al
   contenedor del Collector en `docker-compose.yml`:

   ```yaml
   otel-collector:
     image: otel/opentelemetry-collector-contrib:0.107.0
     environment:
       - HONEYCOMB_API_KEY=${HONEYCOMB_API_KEY}
     env_file:
       - .env   # crea este archivo local, con tus credenciales, y NO lo subas al repo
   ```

4. Reinicia el Collector — ni `cf1` ni `cf2` necesitan reiniciarse ni
   redeployarse por este cambio.

### Doble emisión (exportar a dos backends a la vez)

El Collector permite listar varios exporters en el mismo pipeline:

```yaml
service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo, otlp/honeycomb]   # a los dos, en simultáneo
```

Útil para migrar de un vendor a otro sin cortar el flujo (corres ambos en
paralelo durante la transición), o para tener un backend self-hosted como
fuente de verdad y uno SaaS como respaldo/comparación.

## Nivel 3 — Sin Collector, exportando directo desde la app

El Collector es la pieza recomendada, pero no es obligatorio. Si quisieras
que `cf1`/`cf2` exportaran directo a un backend (sin pasar por el
Collector), bastaría con cambiar `OTEL_EXPORTER_OTLP_ENDPOINT` al endpoint
del backend y, si requiere autenticación, agregar los headers
correspondientes en el exporter del SDK:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

exporter = OTLPSpanExporter(
    endpoint="https://api.honeycomb.io:443",
    headers={"x-honeycomb-team": os.environ["HONEYCOMB_API_KEY"]},
)
```

Esto funciona, pero pierdes las ventajas de tener un Collector centralizado
(cambiar de backend sin redeployar servicios, procesamiento común, etc.) —
ver [[02 Fundamentos de OpenTelemetry]] para el detalle de por qué el
Collector es la pieza recomendada en cualquier arquitectura con más de un
servicio.

## Tabla resumen: qué tan grande es el cambio

| Cambio | Qué tocas |
|---|---|
| Cambiar de Tempo a Jaeger (self-hosted) | Solo `exporters` en la config del Collector |
| Agregar un backend SaaS | `exporters` del Collector + credenciales como variable de entorno |
| Exportar a dos backends a la vez | Agregar el segundo exporter a la lista del pipeline |
| Saltarte el Collector | `OTEL_EXPORTER_OTLP_ENDPOINT` + headers en el SDK de cada servicio |
| Cambiar el código de `cf1`/`cf2` | **Nunca, en ninguno de los casos anteriores** |

## Siguiente paso

Ya viste cómo cambia el destino. [[08 Adaptar a tu Stack]] cubre el otro
eje: cómo se ve esta misma instrumentación en otros lenguajes y otros
entornos de cómputo, no solo Python + Flask + contenedores locales.
