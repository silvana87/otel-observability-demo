# Monitoreo vs Observabilidad

Antes de hablar de OpenTelemetry conviene separar dos ideas que suelen
mezclarse: **monitoreo** y **observabilidad**. No son sinónimos, y la
diferencia no es solo semántica — determina qué preguntas puedes responder
cuando algo falla.

## Monitoreo

**Definición:** proceso de recolectar y analizar datos (métricas, logs) para
detectar cuándo un sistema se desvía de un comportamiento esperado, usando
umbrales y alertas predefinidas.

**Responde:** *"¿Está funcionando el sistema?"*

**Ejemplo típico:** una alerta que se dispara cuando la CPU supera el 80%, o
cuando un servicio falla más de X veces en 5 minutos.

Sus dos pilares clásicos:

| Pilar | Qué captura |
|---|---|
| Métricas | CPU, memoria, latencia, tasa de error — valores numéricos agregados en el tiempo |
| Logs | Eventos discretos, por servicio, generalmente sin correlación entre sí |

## Observabilidad

**Definición:** propiedad de un sistema que permite entender su estado
interno completo a partir de sus señales externas (métricas, logs, trazas),
**incluso ante fallos que nunca anticipaste**.

**Responde:** *"¿Por qué está pasando esto?"*

Se apoya en tres pilares — los mismos dos de monitoreo, más uno:

| Pilar | Qué captura |
|---|---|
| Métricas | (igual que en monitoreo) |
| Logs | (igual que en monitoreo) |
| **Trazas** | El recorrido completo de una operación a través de múltiples servicios, dividido en unidades llamadas *spans* — ver [[02 Fundamentos de OpenTelemetry]] |

Las trazas son el pilar que normalmente falta en un stack de monitoreo
tradicional, y es justo lo que permite pasar de "algo está lento" a
"esto específicamente es lo que está lento, y aquí está la cadena completa
de llamadas que lo prueba".

## Tabla comparativa

| | Monitoreo | Observabilidad |
|---|---|---|
| Pregunta que responde | ¿Algo está mal? | ¿Por qué está mal? |
| Basado en | Umbrales conocidos | Exploración de datos correlacionados |
| Detecta | Fallos anticipados | Fallos anticipados **y** desconocidos |
| Pilar clave adicional | — | Trazas distribuidas |

## ¿Cuándo necesitas observabilidad, y no solo monitoreo?

- **Monitoreo puede ser suficiente** en sistemas monolíticos o de pocos
  componentes, donde los modos de fallo son relativamente conocidos y
  acotados.
- **Observabilidad se vuelve necesaria** cuando hay múltiples servicios,
  lenguajes, o saltos de red entre sistemas — arquitecturas de
  microservicios, sistemas serverless orientados a eventos (funciones que
  se disparan entre sí vía colas o tópicos), o cualquier escenario donde
  un error de latencia o de negocio puede originarse en cualquier punto de
  una cadena de llamadas. Sin trazas distribuidas, correlacionar logs
  sueltos de cada servicio a mano es lento y propenso a error — exactamente
  el problema que resuelve este demo (ver [[05 Explicacion del Codigo]]).

## Siguiente paso

Ahora que está claro *qué* problema resuelve la observabilidad, la
siguiente pregunta es *cómo* — ahí entra OpenTelemetry:
continúa con [[02 Fundamentos de OpenTelemetry]].
