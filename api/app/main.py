"""API CRUD de productos, Parcial 2 de Sistemas Distribuidos.

Corre como un Deployment de 2 réplicas detrás de un Service LoadBalancer y
guarda los datos en PostgreSQL (otro Deployment con un volumen persistente).
"""

import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Producto
from .schemas import InfoOut, ProductoCreate, ProductoOut, ProductoPatch

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("api-crud")

# Kubernetes inyecta estos valores con la Downward API (ver k8s/20-api-deployment.yaml).
POD_NAME = os.getenv("POD_NAME") or socket.gethostname()
POD_IP = os.getenv("POD_IP")
NODE_NAME = os.getenv("NODE_NAME")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DB_HOST = os.getenv("DB_HOST", "localhost")

STATIC_DIR = Path(__file__).parent / "static"


def init_db(intentos: int = 30, espera: float = 2.0) -> None:
    """Crea las tablas, reintentando mientras PostgreSQL arranca.

    Los reintentos también cubren la carrera entre las 2 réplicas de la API
    intentando crear la misma tabla al mismo tiempo.
    """
    for intento in range(1, intentos + 1):
        try:
            Base.metadata.create_all(engine)
            log.info("Base de datos lista (pod %s)", POD_NAME)
            return
        except SQLAlchemyError as exc:
            log.warning(
                "BBDD no disponible (intento %s/%s): %s",
                intento,
                intentos,
                exc.__class__.__name__,
            )
            time.sleep(espera)
    raise RuntimeError("No fue posible conectar con la base de datos")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="API CRUD · Parcial 2 Sistemas Distribuidos",
    description=(
        "CRUD de productos desplegado en Kubernetes: 2 réplicas de la API detrás de "
        "un LoadBalancer y PostgreSQL con volumen persistente.\n\n"
        "Cada respuesta trae el header **X-Served-By** con el pod que la atendió."
    ),
    version=APP_VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def served_by(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Served-By"] = POD_NAME
    # kube-proxy balancea por conexión TCP, no por petición HTTP. Cerrando la
    # conexión en cada respuesta de /api, cada petición del navegador vuelve a
    # pasar por el balanceador y se ve cómo se reparten entre los pods.
    if request.url.path.startswith("/api/"):
        response.headers["Connection"] = "close"
    return response


# --------------------------------------------------------------------------- #
# Salud (las usan las probes de Kubernetes)
# --------------------------------------------------------------------------- #


@app.get("/health", tags=["salud"], summary="Liveness: el proceso está vivo")
def health():
    return {"status": "ok", "pod": POD_NAME}


@app.get("/ready", tags=["salud"], summary="Readiness: hay conexión con la BBDD")
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "sin-bbdd", "pod": POD_NAME},
        )
    return {"status": "ready", "pod": POD_NAME}


@app.get("/api/info", response_model=InfoOut, tags=["salud"], summary="Qué pod respondió")
def info(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Producto)) or 0
    return InfoOut(
        pod=POD_NAME,
        pod_ip=POD_IP,
        nodo=NODE_NAME,
        version=APP_VERSION,
        bbdd_host=DB_HOST,
        productos_en_bbdd=total,
    )


# --------------------------------------------------------------------------- #
# CRUD de productos
# --------------------------------------------------------------------------- #


def _get_or_404(db: Session, producto_id: int) -> Producto:
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail=f"Producto {producto_id} no encontrado")
    return producto


@app.get("/api/productos", response_model=list[ProductoOut], tags=["productos"])
def listar_productos(
    q: str | None = Query(default=None, description="Buscar por nombre o descripción"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Producto).order_by(Producto.id)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Producto.nombre.ilike(patron), Producto.descripcion.ilike(patron)))
    return db.scalars(stmt.limit(limit).offset(offset)).all()


@app.get("/api/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, producto_id)


@app.post(
    "/api/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["productos"],
)
def crear_producto(datos: ProductoCreate, response: Response, db: Session = Depends(get_db)):
    producto = Producto(**datos.model_dump(), creado_por=POD_NAME, actualizado_por=POD_NAME)
    db.add(producto)
    db.commit()
    db.refresh(producto)
    response.headers["Location"] = f"/api/productos/{producto.id}"
    return producto


@app.put("/api/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def reemplazar_producto(producto_id: int, datos: ProductoCreate, db: Session = Depends(get_db)):
    producto = _get_or_404(db, producto_id)
    for campo, valor in datos.model_dump().items():
        setattr(producto, campo, valor)
    producto.actualizado_por = POD_NAME
    db.commit()
    db.refresh(producto)
    return producto


@app.patch("/api/productos/{producto_id}", response_model=ProductoOut, tags=["productos"])
def actualizar_producto(producto_id: int, datos: ProductoPatch, db: Session = Depends(get_db)):
    producto = _get_or_404(db, producto_id)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    producto.actualizado_por = POD_NAME
    db.commit()
    db.refresh(producto)
    return producto


@app.delete(
    "/api/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["productos"],
)
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = _get_or_404(db, producto_id)
    db.delete(producto)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------------- #
# Interfaz web
# --------------------------------------------------------------------------- #


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})
