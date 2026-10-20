def test_health_y_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "pod": "pod-de-prueba"}


def test_header_x_served_by(client):
    r = client.get("/api/info")
    assert r.status_code == 200
    assert r.headers["X-Served-By"] == "pod-de-prueba"
    assert r.json()["pod"] == "pod-de-prueba"


def test_crud_completo(client):
    # CREATE
    r = client.post(
        "/api/productos",
        json={"nombre": "Teclado", "descripcion": "Mecánico", "precio": 189900, "stock": 5},
    )
    assert r.status_code == 201
    creado = r.json()
    pid = creado["id"]
    assert creado["creado_por"] == "pod-de-prueba"
    assert r.headers["Location"] == f"/api/productos/{pid}"

    # READ (uno y lista)
    assert client.get(f"/api/productos/{pid}").json()["nombre"] == "Teclado"
    assert any(p["id"] == pid for p in client.get("/api/productos").json())
    assert client.get("/api/productos", params={"q": "mecán"}).json()[0]["id"] == pid

    # UPDATE parcial (PATCH)
    r = client.patch(f"/api/productos/{pid}", json={"stock": 42})
    assert r.status_code == 200
    assert r.json()["stock"] == 42
    assert r.json()["nombre"] == "Teclado"

    # UPDATE completo (PUT)
    r = client.put(
        f"/api/productos/{pid}",
        json={"nombre": "Mouse", "descripcion": None, "precio": 59900, "stock": 1},
    )
    assert r.status_code == 200
    assert r.json()["nombre"] == "Mouse"
    assert r.json()["descripcion"] is None

    # DELETE
    assert client.delete(f"/api/productos/{pid}").status_code == 204
    assert client.get(f"/api/productos/{pid}").status_code == 404


def test_validaciones(client):
    assert client.post("/api/productos", json={"nombre": "", "precio": 1}).status_code == 422
    assert client.post("/api/productos", json={"nombre": "X", "precio": -5}).status_code == 422
    assert client.patch("/api/productos/999999", json={"stock": 1}).status_code == 404
    assert client.delete("/api/productos/999999").status_code == 404


def test_interfaz_web(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
