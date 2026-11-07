from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    print("✅ /health OK")


def test_create_task():
    resp = client.post("/tasks", json={
        "framework": "cpu_local",
        "circuit_description": "Circuito de prueba con Hadamard y CNOT",
        "shots": 256,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["status"] in ("planned", "code_generated", "completed", "failed_execution")
    task_id = data["task_id"]

    # Consultar estado
    resp2 = client.get(f"/tasks/{task_id}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["task_id"] == task_id
    print(f"✅ POST/GET /tasks OK: {task_id} -> {data2['status']}")


def test_create_task_containment():
    resp = client.post("/tasks", json={
        "framework": "cpu_local",
        "circuit_description": "Circuito hostil con bucle infinito",
        "shots": 100,
        "containment_test": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    task_id = data["task_id"]
    # Esperar un poco para que se ejecute
    import time
    time.sleep(2)
    resp2 = client.get(f"/tasks/{task_id}")
    data2 = resp2.json()
    assert data2["result"]["containment_triggered"] is True or data2["result"]["sandbox_destroyed"] is True
    print(f"✅ Contención OK: task {task_id} contenida={data2['result']['containment_triggered']}")


if __name__ == "__main__":
    test_health()
    test_create_task()
    test_create_task_containment()
    print("\n✅ Todos los tests de API pasaron")
