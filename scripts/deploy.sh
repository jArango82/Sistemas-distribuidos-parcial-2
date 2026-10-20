#!/usr/bin/env bash
# Construye la imagen de la API y despliega todo en el clúster de kubectl actual.
# Uso: ./scripts/deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="parcial2-api:1.0.0"
NS="parcial2"
CONTEXT="$(kubectl config current-context)"

echo "==> Contexto de Kubernetes: $CONTEXT"
echo "==> Construyendo la imagen $IMAGE"
case "$CONTEXT" in
  minikube*)
    # Construye directamente dentro de minikube (no hace falta un registry).
    minikube image build -t "$IMAGE" "$ROOT/api" ;;
  kind-*)
    docker build -t "$IMAGE" "$ROOT/api"
    kind load docker-image "$IMAGE" --name "${CONTEXT#kind-}" ;;
  *)
    # Docker Desktop comparte las imágenes locales con su Kubernetes.
    docker build -t "$IMAGE" "$ROOT/api" ;;
esac

echo "==> Aplicando manifiestos de k8s/"
kubectl apply -f "$ROOT/k8s/"

echo "==> Esperando a PostgreSQL..."
kubectl -n "$NS" rollout status deployment/postgres --timeout=180s
echo "==> Esperando a la API (2 réplicas)..."
kubectl -n "$NS" rollout status deployment/api-crud --timeout=180s

echo
kubectl -n "$NS" get deploy,pods,svc,pvc -o wide
kubectl get pv postgres-pv
echo
echo "Listo. Para entrar a la API ver el paso 5 del README."
