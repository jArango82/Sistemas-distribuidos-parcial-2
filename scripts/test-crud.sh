#!/usr/bin/env bash
# Prueba el CRUD completo contra la API y muestra qué pod atendió cada petición.
# Uso: ./scripts/test-crud.sh [URL]       (por defecto http://localhost)
set -euo pipefail

URL="${1:-${API_URL:-http://localhost}}"
URL="${URL%/}"

# Muestra JSON bonito; si la respuesta no es JSON la imprime tal cual.
pretty() {
  if command -v jq >/dev/null; then jq . <<<"$1" 2>/dev/null || echo "$1"
  else python3 -m json.tool <<<"$1" 2>/dev/null || echo "$1"; fi
}
campo() { python3 -c "import sys, json; print(json.load(sys.stdin)['$1'])"; }

# Hace la petición, imprime método/ruta/código/pod y deja el cuerpo en $BODY.
req() {
  local method="$1" path="$2" data="${3:-}" headers code pod
  headers="$(mktemp)"
  if [[ -n "$data" ]]; then
    BODY="$(curl -sS -X "$method" "$URL$path" -H 'Content-Type: application/json' -d "$data" -D "$headers" -w '\n%{http_code}')"
  else
    BODY="$(curl -sS -X "$method" "$URL$path" -D "$headers" -w '\n%{http_code}')"
  fi
  code="$(tail -n1 <<<"$BODY")"
  BODY="$(sed '$d' <<<"$BODY")"
  pod="$(grep -i '^x-served-by:' "$headers" | awk '{print $2}' | tr -d '\r')"
  rm -f "$headers"
  printf '\n\033[1m%-6s %s\033[0m → HTTP %s  (pod: %s)\n' "$method" "$path" "$code" "${pod:-?}"
  if [[ -n "$BODY" ]]; then pretty "$BODY"; fi
  [[ "$code" == "${4:-2}"* ]] || { echo "ERROR: se esperaba HTTP ${4:-2xx} y llegó $code"; exit 1; }
}

echo "Probando la API en $URL"
req GET  /api/info
req POST /api/productos '{"nombre":"Teclado mecánico","descripcion":"Switches rojos","precio":189900,"stock":10}'
ID="$(campo id <<<"$BODY")"
req GET   /api/productos
req GET   "/api/productos/$ID"
req PATCH "/api/productos/$ID" '{"stock":7}'
req PUT   "/api/productos/$ID" '{"nombre":"Teclado mecánico TKL","descripcion":"Switches marrones","precio":209900,"stock":7}'
req DELETE "/api/productos/$ID"
req GET   "/api/productos/$ID" "" 404

echo
echo "OK: create, read, update y delete funcionan."
