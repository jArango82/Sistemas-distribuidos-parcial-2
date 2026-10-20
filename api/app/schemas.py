from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductoBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=120, examples=["Teclado mecánico"])
    descripcion: str | None = Field(
        default=None, max_length=1000, examples=["Switches rojos, RGB"]
    )
    precio: float = Field(ge=0, examples=[189900])
    stock: int = Field(default=0, ge=0, examples=[15])


class ProductoCreate(ProductoBase):
    """Cuerpo para crear (POST) o reemplazar completamente (PUT) un producto."""


class ProductoPatch(BaseModel):
    """Cuerpo para actualización parcial (PATCH): solo se cambian los campos enviados."""

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = Field(default=None, max_length=1000)
    precio: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)


class ProductoOut(ProductoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creado_por: str | None = None
    actualizado_por: str | None = None
    creado_en: datetime | None = None
    actualizado_en: datetime | None = None


class InfoOut(BaseModel):
    pod: str
    pod_ip: str | None
    nodo: str | None
    version: str
    bbdd_host: str
    productos_en_bbdd: int
