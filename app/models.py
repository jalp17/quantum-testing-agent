from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class Framework(str, Enum):
    QISKIT = "qiskit"
    PENNYLANE = "pennylane"
    CIRQ = "cirq"
    AZURE = "azure"
    CPU_LOCAL = "cpu_local"


class TaskStatus(str, Enum):
    CREATED = "created"
    PLANNED = "planned"
    CODE_GENERATED = "code_generated"
    SANDBOX_RAISED = "sandbox_raised"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED_PLAN = "failed_plan"
    FAILED_EXECUTION = "failed_execution"
    VERIFIED = "verified"
    RESULT_READY = "result_ready"


class CircuitSpec(BaseModel):
    """Especificación de circuito cuántico enviada por el usuario."""
    framework: Framework
    circuit_description: str = Field(..., description="Descripción del circuito en lenguaje natural o QASM")
    shots: int = Field(default=1024, ge=1, le=8192)
    backend: Optional[str] = Field(default=None, description="Backend remoto opcional (ibm, aws, azure, google)")
    containment_test: bool = Field(default=False, description="Si True, activa prueba de contención con código hostil")


class TaskResult(BaseModel):
    """Resultado verificable de una tarea de prueba cuántica."""
    task_id: str
    status: TaskStatus
    framework: Framework
    generated_code: Optional[str] = None
    execution_output: Optional[str] = None
    execution_error: Optional[str] = None
    return_code: Optional[int] = None
    containment_triggered: bool = False
    sandbox_destroyed: bool = False
    execution_time_seconds: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskCreateResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[TaskResult] = None


class PlanStep(BaseModel):
    step: int
    action: str
    details: str


class ExecutionPlan(BaseModel):
    task_id: str
    steps: List[PlanStep]
    framework: Framework
    estimated_time_seconds: int


# Almacenamiento en memoria (MVP). En producción usar base de datos.
_tasks: Dict[str, TaskResult] = {}
_plans: Dict[str, ExecutionPlan] = {}
