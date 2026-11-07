import asyncio
import pytest
from app.orchestrator import plan_task, generate_code
from app.models import CircuitSpec


@pytest.mark.asyncio
async def test_plan_task():
    spec = CircuitSpec(
        framework="qiskit",
        circuit_description="Circuito de 3 qubits con Hadamard y CNOT, medir en base Z",
        shots=1024,
    )
    plan = await plan_task(spec, "test-task-001")
    assert plan.task_id == "test-task-001"
    assert len(plan.steps) > 0
    assert plan.framework == spec.framework
    print(f"✅ plan_task OK: {len(plan.steps)} pasos, framework={plan.framework}")


@pytest.mark.asyncio
async def test_generate_code():
    from app.orchestrator import ExecutionPlan
    spec = CircuitSpec(
        framework="cpu_local",
        circuit_description="Circuito simple de 2 qubits",
        shots=256,
    )
    plan = ExecutionPlan(
        task_id="test-task-002",
        steps=[],
        framework="cpu_local",
        estimated_time_seconds=30,
    )
    code = await generate_code(spec, plan)
    assert code is not None
    assert len(code) > 0
    assert "RESULTADO_CPU_LOCAL" in code or "resultado" in code.lower()
    print(f"✅ generate_code OK: {len(code)} caracteres")


def test_store_and_get():
    from app.store import create_task, get_task, update_task_status, store_result
    from app.models import TaskResult, TaskStatus, CircuitSpec
    from datetime import datetime

    task_id = create_task(CircuitSpec(
        framework="cpu_local",
        circuit_description="test",
        shots=10,
    ))
    task = get_task(task_id)
    assert task is not None
    assert task.status == TaskStatus.CREATED
    assert task.task_id == task_id
    print(f"✅ store/get OK: tarea {task_id} creada")


if __name__ == "__main__":
    asyncio.run(test_plan_task())
    asyncio.run(test_generate_code())
    test_store_and_get()
    print("\n✅ Todos los tests básicos pasaron")
