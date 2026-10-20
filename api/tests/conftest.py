import os
import tempfile

import pytest

# Las pruebas usan SQLite para no depender de un PostgreSQL corriendo.
# Debe definirse ANTES de importar la app (el engine se crea al importar).
_db_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_db_dir}/test.db"
os.environ["POD_NAME"] = "pod-de-prueba"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
