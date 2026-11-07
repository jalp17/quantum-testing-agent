from .models import _tasks, _plans, TaskResult, TaskStatus, ExecutionPlan, PlanStep, CircuitSpec
import uuid
from datetime import datetime, timezone


def create_task(spec: CircuitSpec) -> str:
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    _tasks[task_id] = TaskResult(
        task_id=task_id,
        status=TaskStatus.CREATED,
        framework=spec.framework,
        created_at=now,
    )
    return task_id


def get_task(task_id: str) -> Optional[TaskResult]:
    return _tasks.get(task_id)


def update_task_status(task_id: str, status: TaskStatus) -> None:
    task = _tasks.get(task_id)
    if task:
        task.status = status


def store_plan(task_id: str, plan: ExecutionPlan) -> None:
    _plans[task_id] = plan
    update_task_status(task_id, TaskStatus.PLANNED)


def get_plan(task_id: str) -> Optional[ExecutionPlan]:
    return _plans.get(task_id)


def store_result(task_id: str, result: TaskResult) -> None:
    _tasks[task_id] = result
