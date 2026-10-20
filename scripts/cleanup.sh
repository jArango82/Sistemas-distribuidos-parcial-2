#!/usr/bin/env bash
# Elimina todo lo desplegado (namespace parcial2 y el PersistentVolume).
# Los archivos de la BBDD quedan en el nodo (/data/parcial2-postgres) por la
# política Retain: si vuelves a desplegar, los productos siguen ahí.
# Para borrarlos también en minikube:  minikube ssh -- sudo rm -rf /data/parcial2-postgres
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kubectl delete -f "$ROOT/k8s/" --ignore-not-found
echo "🧹 Recursos eliminados."
