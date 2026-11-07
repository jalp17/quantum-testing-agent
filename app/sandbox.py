import docker
import os
import time
import threading
from typing import Optional, Tuple
from .models import TaskResult, TaskStatus
from .store import _tasks, update_task_status, store_result


SANDBOX_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "60"))
SANDBOX_MEMORY = os.getenv("SANDBOX_MEMORY_LIMIT", "512m")
SANDBOX_CPU = float(os.getenv("SANDBOX_CPU_LIMIT", "1.0"))
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")


class DockerSandbox:
    """Ejecuta código cuántico en un contenedor Docker aislado con límites estrictos."""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception:
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def execute(self, code: str, task_id: str) -> Tuple[Optional[str], Optional[str], Optional[int], bool, float]:
        """
        Ejecuta código en un contenedor Docker desechable.

        Returns:
            (stdout, stderr, return_code, containment_triggered, execution_time)
        """
        start = time.time()
        containment = False

        if not self.is_available():
            # Modo fallback sin Docker: ejecutar localmente (solo para desarrollo)
            return self._local_fallback(code, task_id, start)

        container = None
        try:
            container = self.client.containers.run(
                image=SANDBOX_IMAGE,
                command=["python", "-c", code],
                detach=True,
                mem_limit=SANDBOX_MEMORY,
                cpu_period=100000,
                cpu_quota=int(SANDBOX_CPU * 100000),
                network_disabled=True,
                remove=False,
                stdout=True,
                stderr=True,
            )

            # Esperar con timeout
            try:
                result = container.wait(timeout=SANDBOX_TIMEOUT)
                return_code = result.get("StatusCode", -1)
            except Exception:
                return_code = -1
                containment = True

            # Obtener logs
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

            # Separar stdout/stderr aproximado (Docker los mezcla en logs)
            stdout = logs
            stderr = None

            execution_time = time.time() - start

            # Marcar contención si el código se mató por timeout
            if return_code != 0 and return_code != -1:
                # Código de salida distinto de cero puede indicar error controlado
                pass

            # Destruir contenedor (disciplina de ciclo de vida)
            try:
                container.remove(force=True)
            except Exception:
                pass

            sandbox_destroyed = True

            return stdout, stderr, return_code, containment, execution_time

        except Exception as exc:
            execution_time = time.time() - start
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            return None, str(exc), -1, True, execution_time

    def _local_fallback(self, code: str, task_id: str, start: float) -> Tuple[Optional[str], Optional[str], Optional[int], bool, float]:
        """Ejecuta código localmente cuando Docker no está disponible (desarrollo)."""
        import subprocess
        import tempfile
        import sys

        containment = False
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                tmp_path = f.name

            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=SANDBOX_TIMEOUT,
            )
            return_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr if proc.returncode != 0 else None

            # Limpiar archivo temporal
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            execution_time = time.time() - start
            return stdout, stderr, return_code, containment, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start
            containment = True
            return None, "Timeout: código excedió el límite de tiempo del sandbox", -1, containment, execution_time
        except Exception as exc:
            execution_time = time.time() - start
            return None, str(exc), -1, True, execution_time


_sandbox: Optional[DockerSandbox] = None


def get_sandbox() -> DockerSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox


async def execute_in_sandbox(code: str, task_id: str) -> TaskResult:
    """Ejecuta código en el sandbox y actualiza el estado de la tarea."""
    from .models import TaskStatus
    from .store import update_task_status, store_result, _tasks

    sandbox = get_sandbox()
    stdout, stderr, return_code, containment, exec_time = sandbox.execute(code, task_id)

    task = _tasks.get(task_id)
    if not task:
        raise ValueError(f"Tarea {task_id} no encontrada")

    task.execution_output = stdout
    task.execution_error = stderr
    task.return_code = return_code
    task.containment_triggered = containment
    task.sandbox_destroyed = True
    task.execution_time_seconds = exec_time

    if containment:
        task.status = TaskStatus.FAILED_EXECUTION
    elif return_code == 0:
        task.status = TaskStatus.COMPLETED
    else:
        task.status = TaskStatus.FAILED_EXECUTION

    store_result(task_id, task)
    return task
