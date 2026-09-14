# Arquitectura del Stack Grafana

Este demo usa Grafana + Tempo como backend de visualización/almacenamiento
por defecto — pero conviene entender bien qué es cada pieza, porque es una
fuente común de confusión (y porque en [[07 Integrar Otros Backends]] vas a
ver que ninguna de las dos es obligatoria).

## Grafana no almacena nada

**Grafana es solo la capa de visualización y alerting.** No instrumenta
código, no genera datos, no los almacena — los consulta y los muestra. Es
una UI que sabe hablar con distintos "datasources": Prometheus, Loki,
Tempo, Cloud Monitoring, PostgreSQL, y decenas más.

```
                     ┌──────────────────────────┐
                     │   Grafana — solo UI       │
                     └────────────┬─────────────┘
                                  │  consulta como "datasources"
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       ┌─────────────┐    ┌─────────────┐     ┌─────────────┐
       │  Prometheus  │    │    Loki      │     │    Tempo     │
       │  (métricas)  │    │   (logs)     │     │   (trazas)   │
       └─────────────┘    └─────────────┘     └─────────────┘
```

Estos tres son **procesos/productos separados**, cada uno especializado en
un tipo de señal. Los tres son de Grafana Labs (mismo fabricante), pero
corren como servicios independientes — en el `docker-compose.yml` de este
repo los ves como contenedores distintos (`tempo` y `grafana`), y Grafana
solo sabe hablar con Tempo porque se lo configuramos explícitamente
(`grafana/provisioning/datasources/tempo.yaml`).

## ¿Y por qué Tempo se llama "Tempo"?

Es solo el nombre del producto — Grafana Labs le puso nombres cortos a
cada pieza de su stack (Loki, Tempo, Mimir...), sin relación con la
palabra "temporal". **No es una base de datos "temporal" o efímera** en
ningún sentido especial — sí tiene una ventana de retención configurable
(en este demo, 24 horas, ver `tempo.yaml`), pero eso es estándar en
cualquier sistema de este tipo (Loki y Prometheus también tienen
retención configurable), no algo único de Tempo.

## Cómo funciona Tempo, a alto nivel

1. **Recibe** — expone un receptor OTLP (los mismos puertos 4317/4318 que
   usa el Collector). Puede recibir directo de una app, o —como en este
   demo— del Collector.
2. **Indexa por `trace_id`** — a diferencia de una base de datos de
   propósito general, Tempo está optimizado para un caso muy específico:
   "dame todos los spans que comparten este `trace_id`". Esa simplicidad
   deliberada es parte de por qué es liviano y barato de operar.
3. **Almacena en bloques** — agrupa spans en bloques y los escribe a un
   backend de almacenamiento. En este demo es disco local
   (`backend: local` en `tempo.yaml`), pero en producción normalmente es
   almacenamiento de objetos (S3, GCS, Azure Blob) — no necesita una base
   de datos cara, con object storage barato le alcanza.
4. **Responde queries** — cuando en Grafana buscas por `trace_id` o corres
   una query TraceQL, Grafana se la pasa a Tempo, que busca en sus bloques
   y devuelve los spans que matchean.

## Self-hosted vs Grafana Cloud

Hay dos formas de correr este stack, con implicancias distintas de costo y
operación:

| | Self-hosted | Grafana Cloud |
|---|---|---|
| Quién opera Tempo/Loki/Prometheus | Tú, en tu propia infraestructura | Grafana Labs |
| Escalado y alta disponibilidad | Responsabilidad tuya | Incluido |
| Mantenimiento/actualizaciones | Tú aplicas los upgrades | Automático |
| Retención | La que configures (limitada por tu storage) | Según el plan (14 días en el free tier) |
| Costo | $0 de licencia + infraestructura que operas | Free tier generoso; planes pagos desde ~$19/mes + uso |
| Tiempo para tener algo funcionando | Días (configurar storage, HA, etc.) | Minutos |

Grafana (el núcleo), Loki y Tempo son **open source, licenciados bajo
AGPLv3** desde 2021 (antes eran Apache 2.0). Sigue siendo software libre
—AGPL está aprobada por la OSI—, pero es más "copyleft" que Apache: si
modificas el código y lo ofreces como servicio en red, estás obligado a
compartir esas modificaciones. Para el uso normal (correrlo tal cual, sin
redistribuirlo como producto propio) esto no supone ninguna restricción
práctica.

Este demo usa la variante self-hosted (Tempo + Grafana corriendo en
contenedores locales) porque no requiere ninguna cuenta ni credencial —
pero si tu equipo ya tiene acceso a un tenant de Grafana Cloud
(institucional o personal), puedes apuntar el Collector ahí directamente
sin cambiar nada del código de las aplicaciones — ver
[[07 Integrar Otros Backends]].

## Siguiente paso

Con la teoría cubierta, pasa a [[04 Guia de Instalacion]] para levantar
el demo y ver todo esto funcionando.
