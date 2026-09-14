# Preguntas Frecuentes

Preguntas reales que suelen salir al presentar este material a un equipo,
con respuestas cortas. Cada una enlaza a la página con el detalle completo.

## ¿Grafana es open source?

Sí. El núcleo de Grafana, Loki y Tempo son open source, licenciados bajo
**AGPLv3** desde 2021 (antes eran Apache 2.0). AGPL está aprobada por la
OSI — sigue siendo software libre, aunque más "copyleft" que Apache: si
modificas el código y lo ofreces como servicio en red, debes compartir esas
modificaciones. Para el uso normal (correrlo tal cual) esto no representa
ninguna restricción práctica. Plugins, agentes y algunas librerías se
mantienen en Apache 2.0. Ver [[03 Arquitectura del Stack Grafana]].

## ¿Tiene costo usar Grafana?

Depende de cómo lo uses:

- **Self-hosted** (como en este demo): gratis de licencia — pagas la
  infraestructura que tú operas (cómputo, storage, tiempo de tu equipo).
- **Grafana Cloud** (gestionado): tiene un **free tier genuinamente
  usable** (10,000 series de métricas, 50 GB de logs, 50 GB de trazas, 3
  usuarios, 14 días de retención), y planes pagos desde ~$19/mes + uso
  para más retención y volumen.

Ver [[03 Arquitectura del Stack Grafana]] para la comparación completa.

## ¿Cuál es la diferencia de usar Grafana Cloud vs self-hosted?

La diferencia central es **quién opera la infraestructura de
almacenamiento**, no qué puedes hacer con la herramienta:

| | Self-hosted | Grafana Cloud |
|---|---|---|
| Quién corre Tempo/Loki/Prometheus | Tú | Grafana Labs |
| Escalado, HA, backups | Responsabilidad tuya | Incluido |
| Tiempo para tener algo funcionando | Días | Minutos |

Es común usar un modelo híbrido: Grafana Cloud como UI/alertamiento
gestionado, pero con el almacenamiento de trazas/logs/métricas
autogestionado y conectado como datasource externo — útil cuando el
volumen de datos es alto o se necesita retención más larga que la que
ofrece el plan contratado.

## ¿Tengo que levantar OpenTelemetry para cada proyecto, o puede ser transversal?

Depende de la capa:

- **La instrumentación (el código con spans) vive dentro de cada
  proyecto** — no hay forma de instrumentar desde afuera sin tocar cada
  servicio. Pero esto se resuelve una sola vez con una **librería interna
  compartida** que cada proyecto solo instala y configura con pocas
  líneas, en vez de reimplementar el setup en cada repo.
- **El Collector es transversal por diseño** — un solo Collector (o unos
  pocos, por ejemplo uno por ambiente) recibe telemetría de decenas de
  servicios distintos. No se levanta uno por proyecto.
- **El backend (Tempo/Loki/Prometheus o el proveedor que elijas) es
  completamente transversal** — el mismo tenant para todo el equipo o
  toda la empresa.

En resumen: instrumentación por proyecto (vía librería compartida),
Collector y backend transversales. Ver [[02 Fundamentos de OpenTelemetry]].

## ¿Qué es un span?

La unidad mínima de una traza: una operación con inicio y fin, con nombre,
`trace_id`, `parent_span_id`, atributos, y status. Una traza completa es un
árbol de spans conectados. Ver la sección de spans en
[[02 Fundamentos de OpenTelemetry]] para el detalle completo con ejemplos
de código.

## ¿Por qué Tempo se llama así? ¿Es una base de datos "temporal"?

No — es solo el nombre del producto (como Loki o Mimir), sin relación con
"temporal" en el sentido de efímero. Sí tiene una ventana de retención
configurable, pero eso es estándar en cualquier sistema de este tipo, no
algo especial de Tempo. Ver [[03 Arquitectura del Stack Grafana]].

## ¿Ya tenemos herramientas de observabilidad (agentes de logs, un service
mesh, un SDK de frontend...). ¿Para qué agregar OpenTelemetry?

Depende de qué cubren esas herramientas hoy. Es común que la observabilidad
ya establecida en una empresa use **agentes específicos por tipo de
fuente**: un recolector de logs de contenedor, tracing a nivel de service
mesh (que depende de que haya un sidecar inyectable — no aplica a
funciones serverless efímeras), un SDK propietario para el frontend, un
datasource directo hacia el proveedor cloud para servicios administrados.

Ese patrón cubre muy bien cargas persistentes con infraestructura fija
(pods en un clúster), pero típicamente **no llega a componentes
serverless/event-driven** (funciones que no tienen dónde inyectar un
sidecar, ni un contenedor de larga duración donde correr un agente). Ahí
es donde instrumentar directamente con el SDK de OpenTelemetry se vuelve
necesario: es la única forma de obtener una traza distribuida real (no
solo métricas aisladas por función) cuando no hay infraestructura fija
donde apoyarse.

Un dato adicional: muchas herramientas de frontend RUM (como Grafana Faro)
ya construyen su capacidad de tracing internamente sobre OpenTelemetry —
la tecnología suele estar ya presente, aunque empaquetada por otro
producto.

## ¿Cómo se propaga el trace_id si en el medio hay una cola de mensajería
(Pub/Sub, SQS, Kafka...) en vez de una llamada HTTP directa?

A diferencia de HTTP (donde las librerías de auto-instrumentación
inyectan/leen el header `traceparent` solas), con mensajería hay que
hacerlo a mano con `propagate.inject()` del lado publicador y
`propagate.extract()` del lado consumidor, guardando ese contexto en los
atributos/metadata del mensaje. Ver
[[06 Propagacion de Contexto en Mensajeria]] para el patrón completo con
ejemplos por proveedor.

## ¿Puedo usar esto con [Jaeger / Datadog / Honeycomb / Grafana Cloud /
otro backend]?

Sí — es el punto central de usar un estándar abierto. Ver
[[07 Integrar Otros Backends]] para ejemplos concretos, incluyendo un
stack alternativo funcional con Jaeger incluido en este mismo repo
(`docker-compose.jaeger.yml`).

## No usamos Python/Flask, usamos [Node.js / Java / Go / .NET]. ¿Aplica
igual?

Sí, el patrón conceptual (instrumentación automática + spans manuales +
propagación de contexto + Collector transversal) es igual en cualquier
lenguaje. Ver [[08 Adaptar a tu Stack]] para ejemplos de código en los
lenguajes más comunes, y para entornos serverless/Kubernetes en vez de
contenedores locales.

## ¿Cuál es la diferencia entre monitoreo y observabilidad, en una frase?

Monitoreo responde "¿algo está mal?" con umbrales conocidos; observabilidad
responde "¿por qué está mal?", incluso ante fallos que no anticipaste,
gracias al pilar de trazas distribuidas. Ver
[[01 Monitoreo vs Observabilidad]] para el detalle completo.
