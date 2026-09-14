# Guía de Instalación

## Requisitos

- **Docker** y **Docker Compose** instalados y el daemon de Docker
  corriendo (en Mac/Windows, abre Docker Desktop y espera a que el ícono
  quede fijo antes de continuar).
- Puertos libres en tu máquina: `3000` (Grafana), `3200` (Tempo),
  `4317`/`4318` (Collector), `8081`/`8082` (los dos servicios de ejemplo).
- No necesitas cuenta en ningún proveedor cloud ni credenciales de ningún
  tipo — todo corre local.

Verifica que Docker esté listo antes de seguir:

```bash
docker info
```

Si te devuelve información del sistema (no un error de conexión), estás
listo. Si da error de conexión al daemon, abre Docker Desktop (o inicia el
servicio `docker` en Linux) y reintenta.

## 1. Clonar el repo y levantar el stack

```bash
git clone <url-de-este-repo>
cd <nombre-del-repo>
docker compose up --build
```

La primera vez tarda un poco más porque construye las imágenes de `cf1` y
`cf2` (instala las dependencias de Python). Espera a ver los 5 servicios
corriendo: `cf1`, `cf2`, `otel-collector`, `tempo`, `grafana`.

## 2. Disparar el pipeline

En **otra terminal** (deja la anterior con `docker compose up` corriendo):

```bash
chmod +x trigger.sh   # solo la primera vez
./trigger.sh 3
```

Esto simula 3 disparos del servicio A (equivalente a 3 mensajes reales
llegando desde afuera). Cada uno genera una traza distribuida completa.

## 3. Ver la traza en Grafana

1. Abre **http://localhost:3000** (no pide login).
2. Ve a **Explore** (ícono de brújula en el menú lateral).
3. Selecciona el datasource **Tempo** (ya viene configurado).
4. Click en **Search**, filtra por `Service Name = cf1-extraccion-bigquery`.
5. Abre la traza más reciente y explora el waterfall.

Alternativa más rápida — en el query type **TraceQL**, pega:

```
{ resource.service.name = "cf1-extraccion-bigquery" }
```

## 4. Apagar todo

```bash
docker compose down -v
```

---

## Solución de problemas comunes

Estos son errores reales que salieron al validar este demo — quedan acá
documentados para ahorrarte el mismo tiempo de diagnóstico.

### `Cannot connect to the Docker daemon`

Docker Desktop no está corriendo. Ábrelo y espera a que el ícono de la
ballena quede fijo (no animándose) antes de reintentar `docker compose up`.

### El build falla o los contenedores `cf1`/`cf2` aparecen como `Exited`

Revisa los logs de cada uno:

```bash
docker compose logs cf1
docker compose logs cf2
```

Si ves un traceback de Python terminando en algo como:

```
ModuleNotFoundError: No module named 'pkg_resources'
```

Es un problema conocido de las imágenes `python:3.12-slim` recientes: ya
no traen `setuptools` preinstalado, y algunos paquetes de
`opentelemetry-instrumentation-*` todavía dependen de `pkg_resources`
(que viene de `setuptools`) para resolver dependencias en tiempo de
ejecución. Este repo ya incluye el fix (`setuptools` está en
`requirements.txt` de ambos servicios) — si lo ves de todas formas,
confirma que no tengas una versión vieja cacheada:

```bash
docker compose build --no-cache cf1 cf2
docker compose up
```

### `curl` a `trigger.sh` devuelve `Expecting value: line 1 column 1`

Significa que `cf1` no respondió nada (la respuesta vino vacía). Casi
siempre es consecuencia del problema anterior (el contenedor se cayó al
arrancar). Corre `docker compose ps` — si `cf1` o `cf2` no aparecen como
`Up`, revisa sus logs con el comando de arriba.

### La traza no aparece en Grafana ("No data")

En orden de probabilidad:

1. **No has corrido `trigger.sh` todavía**, o lo corriste pero falló (ver
   arriba). Verifica que te haya devuelto un JSON con `"cf1": "ok"`.
2. **El rango de tiempo** en la esquina superior derecha de Grafana
   Explore está muy acotado — amplíalo a "Last 1 hour" o más.
3. **El Collector no está recibiendo nada.** Revisa sus logs
   (`docker compose logs otel-collector`) — deberías ver líneas con
   spans llegando (por el exporter `debug` configurado). Si no aparece
   nada ahí, el problema está entre `cf1`/`cf2` y el Collector, no en
   Grafana ni Tempo.

### Solo veo los spans de un servicio, no de los dos

Si la traza en Grafana muestra únicamente `cf1` y nunca aparece `cf2`
dentro del mismo árbol, el problema es de propagación de contexto, no de
conectividad. Revisa [[05 Explicacion del Codigo]] — específicamente la
sección de cómo `RequestsInstrumentor` y `FlaskInstrumentor` se encargan
de esto automáticamente en el caso HTTP.

---

## Siguiente paso

Con todo corriendo, [[05 Explicacion del Codigo]] recorre exactamente qué
hace cada archivo y por qué.
