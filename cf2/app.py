"""
CF2 — simula la Cloud Function que recibe el evento de CF1 y lo procesa.

No hace NADA especial para "engancharse" a la traza de CF1: FlaskInstrumentor
lee automáticamente el header `traceparent` que llega en el request y continúa
la misma traza con un span hijo. Esa es, en la práctica, toda la "magia" de
la propagación de contexto: el mecanismo que conecta ambos servicios en una sola traza.
"""

import logging
import os
import time

from flask import Flask, jsonify, request

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [cf2] %(message)s")
log = logging.getLogger("cf2")

OTEL_COLLECTOR_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

resource = Resource.create({"service.name": "cf2-siguiente-paso"})
provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint=OTEL_COLLECTOR_ENDPOINT, insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("cf2")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


def procesar(filas):
    with tracer.start_as_current_span("cf2-processing") as span:
        span.set_attribute("processing.rows_in", filas)
        time.sleep(0.7)
        span.set_attribute("processing.status", "completado")
        return {"filas_procesadas": filas}


@app.route("/process", methods=["POST"])
def process():
    body = request.get_json(force=True) or {}
    filas = body.get("filas", 0)
    log.info("Procesando %s filas (traza continuada automáticamente desde CF1)", filas)
    resultado = procesar(filas)
    return jsonify({"cf2": "ok", "resultado": resultado})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "cf2"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8082)
