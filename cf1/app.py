"""
CF1 — simula la Cloud Function que extrae datos de BigQuery.

Este servicio representa el primer salto de un pipeline típico de extracción de datos:
  BigQuery -> CF1 (extracción/transformación) -> CF2 (siguiente paso)

Está instrumentado con OpenTelemetry:
  - FlaskInstrumentor: crea automáticamente un span por cada request entrante.
  - RequestsInstrumentor: propaga el contexto de traza (header `traceparent`)
    en la llamada HTTP saliente hacia CF2, sin que tengamos que hacerlo a mano.
  - Dos spans manuales (`bigquery-query`, `transform-and-publish`) para
    representar el trabajo interno de la función, igual que se vería si
    instrumentáramos la Cloud Function real.
"""

import logging
import os
import random
import time

import requests
from flask import Flask, jsonify

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [cf1] %(message)s")
log = logging.getLogger("cf1")

OTEL_COLLECTOR_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
CF2_URL = os.environ.get("CF2_URL", "http://cf2:8082/process")

# --- Configuración de OpenTelemetry ---------------------------------------
# service.name es lo que va a identificar a este servicio en Grafana Tempo.
resource = Resource.create({"service.name": "cf1-extraccion-bigquery"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint=OTEL_COLLECTOR_ENDPOINT, insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("cf1")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


def query_bigquery_simulada():
    """Simula una consulta a una fuente de datos (ej. BigQuery), con una duración realista."""
    with tracer.start_as_current_span("bigquery-query") as span:
        duracion = random.uniform(2.0, 2.6)
        span.set_attribute("bq.query", "SELECT * FROM ventas.transacciones WHERE fecha = CURRENT_DATE()")
        span.set_attribute("bq.rows_returned", 18342)
        log.info("Consultando BigQuery (simulado, %.2fs)...", duracion)
        time.sleep(duracion)
        return {"filas": 18342, "duracion_s": round(duracion, 2)}


def transformar_y_publicar(datos):
    """Simula la transformación y el 'publish' del evento hacia CF2."""
    with tracer.start_as_current_span("transform-and-publish") as span:
        time.sleep(0.35)
        span.set_attribute("transform.rows_out", datos["filas"])
        return {"payload_size_kb": 128}


@app.route("/extract", methods=["POST"])
def extract():
    log.info("Iniciando extracción (trigger recibido)")
    datos = query_bigquery_simulada()
    transformar_y_publicar(datos)

    # OJO: no propagamos el trace_id a mano. RequestsInstrumentor inyecta
    # automáticamente el header `traceparent` en esta llamada saliente,
    # esto es lo que se conoce como "propagar el contexto".
    log.info("Invocando a CF2...")
    resp = requests.post(CF2_URL, json={"filas": datos["filas"]}, timeout=30)

    return jsonify({
        "cf1": "ok",
        "bigquery": datos,
        "cf2_response": resp.json(),
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "cf1"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
