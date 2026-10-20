"""Conexión a la base de datos.

En Kubernetes los datos de conexión llegan como variables de entorno:
  - DB_HOST / DB_PORT        -> ConfigMap `api-config`
  - DB_USER / DB_PASSWORD /
    DB_NAME                  -> Secret `postgres-secret`
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def build_database_url() -> str | URL:
    # DATABASE_URL tiene prioridad (útil para pruebas locales con SQLite).
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("DB_USER", "parcial2"),
        password=os.getenv("DB_PASSWORD", "parcial2"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "inventario"),
    )


def make_engine(url: str | URL):
    if str(url).startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # pool_pre_ping descarta conexiones muertas (p. ej. si el pod de la BBDD
    # se reinició) antes de usarlas.
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5)


engine = make_engine(build_database_url())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
