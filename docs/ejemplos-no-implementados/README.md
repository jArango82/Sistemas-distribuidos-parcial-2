# Ejemplos no implementados

Estos archivos acompañan la investigación del **punto 4**
([`../punto-4-replicas-y-balanceo-bbdd.md`](../punto-4-replicas-y-balanceo-bbdd.md)).
El enunciado pide solo investigar, así que no forman parte del despliegue:
`scripts/deploy.sh` y `kubectl apply -f k8s/` nunca los aplican.

| Archivo | Qué ilustra |
|---|---|
| [`statefulset-postgres.yaml`](statefulset-postgres.yaml) | Cómo se vería PostgreSQL con StatefulSet: un volumen por réplica, DNS estable y Services separados para lecturas/escrituras. |
| [`cloudnativepg-cluster.yaml`](cloudnativepg-cluster.yaml) | La opción recomendada: un Operator que crea primario + réplicas, failover y Services `-rw` / `-ro` por nosotros. |
