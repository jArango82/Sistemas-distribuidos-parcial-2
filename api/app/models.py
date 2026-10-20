from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, default=None)
    precio: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    # Qué pod de la API hizo la operación: demuestra que las dos réplicas
    # comparten la misma base de datos.
    creado_por: Mapped[str | None] = mapped_column(String(253), default=None)
    actualizado_por: Mapped[str | None] = mapped_column(String(253), default=None)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
