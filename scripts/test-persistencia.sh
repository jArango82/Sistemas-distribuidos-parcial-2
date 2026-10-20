#!/usr/bin/env bash
# Demuestra que los datos sobreviven aunque el pod de PostgreSQL muera,
# gracias al PersistentVolume.
#   1. Inserta un registro directamente en PostgreSQL.
#   2. Elimina el pod de la BBDD (Kubernetes crea uno nuevo, con otro nombre).
#   3. Consulta el registro desde el pod nuevo.
set -euo pipefail

NS="parcial2"
MARCA="persistencia-$(date +%s)"

pod_bbdd() { kubectl -n "$NS" get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}'; }
psql_en() { kubectl -n "$NS" exec "$1" -- sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -tA -c \"$2\""; }

POD_VIEJO="$(pod_bbdd)"
echo "1️⃣  Pod actual de la BBDD: $POD_VIEJO"
psql_en "$POD_VIEJO" "INSERT INTO productos (nombre, precio, stock, creado_por) VALUES ('$MARCA', 1, 1, 'test-persistencia');" >/dev/null
echo "    Insertado el producto '$MARCA'"

echo "2️⃣  Eliminando el pod $POD_VIEJO ..."
kubectl -n "$NS" delete pod "$POD_VIEJO" --wait=true
kubectl -n "$NS" rollout status deployment/postgres --timeout=180s
kubectl -n "$NS" wait --for=condition=Ready pod -l app=postgres --timeout=180s
POD_NUEVO="$(pod_bbdd)"
echo "    Pod nuevo de la BBDD: $POD_NUEVO"

echo "3️⃣  Buscando el producto en el pod nuevo..."
ENCONTRADO="$(psql_en "$POD_NUEVO" "SELECT nombre FROM productos WHERE nombre = '$MARCA';")"
if [[ "$ENCONTRADO" == "$MARCA" ]]; then
  echo "✅ El dato sobrevivió a la muerte del pod: el volumen funciona."
  psql_en "$POD_NUEVO" "DELETE FROM productos WHERE nombre = '$MARCA';" >/dev/null
else
  echo "❌ No se encontró el dato: revisa el PV/PVC."
  exit 1
fi
