# Explicación del Código

## Arquitectura

El demo tiene 5 piezas corriendo en contenedores separados, en dos grupos:

**El pipeline que se instrumenta:**
- `cf1` — simula un servicio que extrae datos de una fuente externa
  (en el ejemplo, algo parecido a una consulta a BigQuery)
- `cf2` — simula un segundo servicio que procesa el resultado

**El backend de observabilidad:**
- `otel-collector` — recibe la telemetría que emiten `cf1` y `cf2`
- `tempo` — la almacena
- `grafana` — la visualiza (con Tempo configurado como datasource)

```
                    ┌─────────────┐
   trigger.sh  ───► │     cf1     │
   (simula el       │ :8081       │
    disparo real)   └──────┬──────┘
                            │ POST /process
                            │ (con header traceparent)
                            ▼
                     ┌─────────────┐
                     │     cf2     │
                     │ :8082       │
                     └──────┬──────┘
                            │
        ambos exportan sus spans vía OTLP/gRPC
                            │
                            ▼
                  ┌───────────────────┐
                  │  otel-collector    │  :4317 (gRPC) / :4318 (HTTP)
                  └─────────┬──────────┘
                            │ reenvía a Tempo
                            ▼
                     ┌─────────────┐
                     │    tempo    │  :3200
                     └──────┬──────┘
                            │ Grafana lo consulta como datasource
                            ▼
                     ┌─────────────┐
                     │   grafana   │  :3000
                     └─────────────┘
```

## El flujo paso a paso

1. **`trigger.sh` hace `curl -X POST http://localhost:8081/extract`** —
   simula el evento que en un caso real dispararía el primer servicio (un
   mensaje de cola, un cron, un webhook). Es el único paso manual; todo lo
   demás pasa solo.

2. **El request llega a `cf1/app.py`, ruta `/extract`.** Como
   `FlaskInstrumentor().instrument_app(app)` está activo, OpenTelemetry
   crea automáticamente un span raíz para este request entrante — sin que
   se haya escrito código explícito para eso.

3. **Dentro de `extract()`, se llama a una función que simula el trabajo
   de extracción**, abriendo un span manual:

   ```python
   with tracer.start_as_current_span("bigquery-query") as span:
       span.set_attribute("bq.rows_returned", 18342)
       time.sleep(duracion)
       # al salir del "with", el span se cierra automáticamente:
       # aquí OTel calcula la duración y lo deja listo para exportar
   ```

   El `with` ES el span: abre el reloj al entrar, lo cierra al salir. Todo
   lo que pase adentro (incluyendo llamadas a funciones que abran sus
   propios spans) queda anidado como hijo.

4. **Luego se llama a una segunda función** (`transformar_y_publicar`),
   mismo patrón: otro span manual.

5. **El paso clave: una llamada HTTP saliente hacia `cf2`.** Es un
   `requests.post(...)` normal — pero como `RequestsInstrumentor` está
   activo, OTel intercepta esa llamada e inyecta automáticamente el header
   `traceparent` (con el `trace_id` actual + el `span_id` del span
   activo). **Nunca se escribe ese header a mano.** Esto es la
   "propagación de contexto" de la que habla
   [[02 Fundamentos de OpenTelemetry]].

6. **El request llega a `cf2/app.py`, ruta `/process`.**
   `FlaskInstrumentor` en `cf2` lee ese header `traceparent` entrante y,
   en vez de crear una traza nueva, **continúa la misma traza** con un
   span hijo. Esto es lo que hace que en Grafana aparezca **un solo
   árbol** con dos servicios distintos adentro, en vez de dos trazas
   sueltas y sin relación.

7. **Dentro de `process()` se abre el último span manual**, simulando el
   procesamiento.

8. **Cada servicio tiene un `BatchSpanProcessor`** que junta sus spans y
   los envía por OTLP/gRPC al `otel-collector` (puerto 4317) en lotes, no
   span por span — por eso a veces hay un pequeño delay entre que termina
   el request y que la traza "aparece" en Grafana.

9. **El Collector** recibe por OTLP y reenvía a Tempo — este es el punto
   donde, en un caso real, cambiarías el destino sin tocar `cf1` ni `cf2`
   (ver [[07 Integrar Otros Backends]]).

10. **Tempo almacena y responde queries**, y **Grafana** las consulta
    como datasource.

## Qué hace único a un `trace_id`

El "pegamento" que hace que 6 spans de 2 procesos distintos aparezcan
como una sola traza es el `trace_id`, generado la primera vez que `cf1`
crea el span raíz. Ese mismo `trace_id` viaja en el header `traceparent`
hacia `cf2`, y por eso `cf2` continúa esa traza en vez de empezar una
propia.

## Archivo por archivo

| Archivo | Qué hace |
|---|---|
| `docker-compose.yml` | Orquesta los 5 servicios: red compartida, variables de entorno, orden de arranque (`depends_on`) |
| `cf1/app.py` | Servicio Flask que simula la extracción; instrumentado con `FlaskInstrumentor` + `RequestsInstrumentor` |
| `cf2/app.py` | Servicio Flask que simula el procesamiento; instrumentado con `FlaskInstrumentor` |
| `cf1/requirements.txt`, `cf2/requirements.txt` | Dependencias — incluyen `setuptools` explícito por el problema descrito en [[04 Guia de Instalacion]] |
| `otel-collector-config.yaml` | Config del Collector: qué recibe (`receivers`), cómo procesa (`processors`), a dónde exporta (`exporters`) |
| `tempo.yaml` | Config mínima de Tempo: dónde escucha, dónde almacena los bloques |
| `grafana/provisioning/datasources/tempo.yaml` | Le dice a Grafana, al arrancar, que ya existe un datasource Tempo — por eso no hay que configurarlo a mano la primera vez |
| `trigger.sh` | Script de conveniencia para disparar el pipeline N veces seguidas |

## Variables de entorno relevantes

Definidas en `docker-compose.yml`, se leen en `cf1/app.py` y `cf2/app.py`:

- `OTEL_EXPORTER_OTLP_ENDPOINT` — a dónde exportan los spans (el Collector). Es la variable que cambiarías para apuntar a un backend distinto sin tocar código — ver [[07 Integrar Otros Backends]].
- `CF2_URL` (solo en `cf1`) — la URL a la que `cf1` llama para invocar a `cf2`.

## Siguiente paso

Este demo usa HTTP directo entre servicios, donde la propagación es
automática. Si tu arquitectura real usa una cola de mensajería en el
medio (muy común en sistemas serverless orientados a eventos), la
propagación deja de ser automática — ver
[[06 Propagacion de Contexto en Mensajeria]] para el patrón completo.
