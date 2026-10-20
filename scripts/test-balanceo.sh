#!/usr/bin/env bash
# Envía N peticiones a la API y cuenta cuántas atendió cada pod.
#
# Uso:
#   ./scripts/test-balanceo.sh                  → desde DENTRO del clúster (pod temporal con curl)
#   ./scripts/test-balanceo.sh http://localhost → desde tu máquina, a través del LoadBalancer
#   N=50 ./scripts/test-balanceo.sh             → cambiar el número de peticiones
#
# OJO: no uses `kubectl port-forward` para esta prueba: el port-forward se
# conecta a UN solo pod y no pasa por el balanceo del Service.
set -euo pipefail

N="${N:-40}"
NS="parcial2"

if [[ $# -ge 1 ]]; then
  URL="${1%/}"
  echo "Enviando $N peticiones a $URL/api/info desde esta máquina..."
  RESULTADO="$(for _ in $(seq 1 "$N"); do
    curl -sS -o /dev/null -D - "$URL/api/info" | grep -i '^x-served-by:' | awk '{print $2}' | tr -d '\r'
  done)"
else
  echo "Enviando $N peticiones a http://api-crud-lb/api/info desde un pod dentro del clúster..."
  RESULTADO="$(kubectl -n "$NS" run "balanceo-$RANDOM" --rm -i --quiet --restart=Never \
    --image=curlimages/curl:8.10.1 --command -- sh -c \
    "for i in \$(seq 1 $N); do curl -s -o /dev/null -D - http://api-crud-lb/api/info | grep -i '^x-served-by:' | awk '{print \$2}' | tr -d '\r'; done")"
fi

echo
echo "Peticiones atendidas por cada pod:"
sort <<<"$RESULTADO" | uniq -c | sort -rn
PODS="$(sort -u <<<"$RESULTADO" | grep -c .)"
echo
if [[ "$PODS" -ge 2 ]]; then
  echo "OK: el Service repartió la carga entre $PODS pods."
else
  echo "ERROR: todas las peticiones llegaron a un solo pod. Revisar que las 2 réplicas estén Ready."
  exit 1
fi
