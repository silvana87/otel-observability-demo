#!/usr/bin/env bash
# Simula el trigger que hoy inicia CF1 (ej. un mensaje de Pub/Sub o un cron).
# Cada ejecución genera UNA traza distribuida completa: CF1 -> CF2.

set -euo pipefail

N=${1:-1}

for i in $(seq 1 "$N"); do
  echo "--- Disparo $i/$N ---"
  curl -s -X POST http://localhost:8081/extract | python3 -m json.tool
  echo
  sleep 1
done

echo "Listo. Abre Grafana en http://localhost:3000 -> Explore -> datasource Tempo"
echo "y busca por service.name = cf1-extraccion-bigquery para ver la traza."
