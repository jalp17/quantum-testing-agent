from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from .models import CircuitSpec, TaskCreateResponse, TaskStatusResponse
from .store import create_task, get_task, update_task_status
from .orchestrator import orchestrate
from .sandbox import execute_in_sandbox
from .backend_adapters import get_adapter


app = FastAPI(
    title="Quantum Testing Agent",
    description="Agente de pruebas cuánticas aislado en sandbox Docker para Vultr Agent Rush Hackathon",
    version="1.0.0",
)

# Montar archivos estáticos (UI) si existen
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/health")
async def health():
    """Estado del servicio."""
    from .sandbox import get_sandbox
    sandbox = get_sandbox()
    return {
        "status": "ok",
        "sandbox_available": sandbox.is_available(),
        "service": "quantum-testing-agent",
    }


@app.post("/tasks", response_model=TaskCreateResponse)
async def create_quantum_task(spec: CircuitSpec):
    """
    Crea una nueva tarea de prueba cuántica.
    Flujo: crear tarea -> planificar (LLM) -> generar código -> ejecutar en sandbox -> verificar.
    """
    task_id = create_task(spec)
    update_task_status(task_id, __import__("app.models", fromlist=["TaskStatus"]).TaskStatus.PLANNED)

    # Planificación y generación de código (orquestador con LLM de Vultr)
    code = await orchestrate(spec, task_id)

    # Ejecución en sandbox Docker aislado
    result = await execute_in_sandbox(code, task_id)

    # Adaptador de backend remoto (informativo, no ejecuta en esta fase)
    adapter = get_adapter(spec.framework.value)
    backend_info = {
        "adapter": adapter.__class__.__name__,
        "available": adapter.is_available(),
    }

    return TaskCreateResponse(
        task_id=task_id,
        status=result.status,
        message=f"Tarea {task_id} creada y ejecutada. Framework: {spec.framework.value}. Backend: {backend_info}",
    )


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Obtiene el estado y resultado de una tarea."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Tarea {task_id} no encontrada")
    return TaskStatusResponse(
        task_id=task_id,
        status=task.status,
        result=task,
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Página principal con UI simple para demo."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Testing Agent — Vultr Agent Rush</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; padding: 2rem; }}
        .container {{ max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #38bdf8; margin-bottom: 1rem; font-size: 1.75rem; }}
        h2 {{ color: #94a3b8; margin-top: 2rem; margin-bottom: 0.75rem; font-size: 1.25rem; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .form-group {{ margin-bottom: 1rem; }}
        label {{ display: block; margin-bottom: 0.375rem; color: #94a3b8; font-size: 0.875rem; }}
        select, input, textarea {{ width: 100%; padding: 0.625rem; background: #0f172a; border: 1px solid #475569; border-radius: 0.375rem; color: #f1f5f9; font-size: 0.875rem; }}
        textarea {{ min-height: 100px; resize: vertical; }}
        button {{ background: #38bdf8; color: #0f172a; border: none; padding: 0.75rem 1.5rem; border-radius: 0.375rem; font-weight: 600; cursor: pointer; font-size: 0.95rem; }}
        button:hover {{ background: #7dd3fc; }}
        button:disabled {{ background: #475569; cursor: not-allowed; }}
        .result {{ background: #0f172a; border: 1px solid #334155; border-radius: 0.375rem; padding: 1rem; margin-top: 1rem; white-space: pre-wrap; font-family: 'SF Mono', Monaco, monospace; font-size: 0.8rem; overflow-x: auto; }}
        .badge {{ display: inline-block; padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 600; margin-left: 0.5rem; }}
        .badge-ok {{ background: #10b981; color: #ffffff; }}
        .badge-fail {{ background: #ef4444; color: #ffffff; }}
        .badge-pending {{ background: #f59e0b; color: #ffffff; }}
        .containment {{ border-left: 4px solid #ef4444; padding-left: 1rem; margin-top: 0.75rem; }}
        .hint {{ color: #64748b; font-size: 0.8rem; margin-top: 0.25rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚛️ Quantum Testing Agent</h1>
        <p style="color:#94a3b8; margin-bottom: 1.5rem;">
            Agente de pruebas cuánticas aislado en sandbox Docker para <strong>Vultr: Agent Rush Hackathon</strong>.<br>
            Desafío: <em>Blast Radius Zero</em> — contención obligatoria.
        </p>

        <div class="card">
            <h2>1. Especificar prueba cuántica</h2>
            <div class="form-group">
                <label for="framework">Framework</label>
                <select id="framework">
                    <option value="qiskit">Qiskit (IBM Quantum)</option>
                    <option value="pennylane">PennyLane (AWS Braket)</option>
                    <option value="cirq">Cirq (Google)</option>
                    <option value="azure">Azure Quantum (Microsoft)</option>
                    <option value="cpu_local">Simulador CPU local (fallback)</option>
                </select>
            </div>
            <div class="form-group">
                <label for="circuit">Descripción del circuito</label>
                <textarea id="circuit" placeholder="Ej: Circuito de 3 qubits con Hadamard en q0, CNOT q0→q1, CNOT q1→q2, medir en base Z. 1024 shots."></textarea>
            </div>
            <div class="form-group">
                <label for="shots">Shots</label>
                <input type="number" id="shots" value="1024" min="1" max="8192">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="containment"> Prueba de contención (código hostil: bucle infinito / rm -rf)
                </label>
                <p class="hint">Activa para demostrar que el sandbox absorbe fallos sin comprometer el host.</p>
            </div>
            <button onclick="runTask()">Ejecutar prueba en sandbox</button>
        </div>

        <div id="status" class="card" style="display:none;">
            <h2>2. Estado de la tarea</h2>
            <div id="taskId" style="color:#94a3b8; font-size:0.8rem;"></div>
            <div id="taskStatus" style="margin:0.5rem 0;"></div>
        </div>

        <div id="result" class="card" style="display:none;">
            <h2>3. Resultado verificable</h2>
            <div id="resultContent" class="result"></div>
        </div>

        <div class="card">
            <h2>Arquitectura</h2>
            <ul style="color:#94a3b8; margin-left:1rem;">
                <li><strong>Backend:</strong> VM Vultr + FastAPI (capa de control y orquestación)</li>
                <li><strong>LLM:</strong> Vultr Serverless Inference (OpenAI-compatible)</li>
                <li><strong>Sandbox:</strong> Docker aislado, límites de CPU/memoria/tiempo, destroy tras tarea</li>
                <li><strong>Frameworks:</strong> Qiskit, PennyLane, Cirq, Azure Quantum, CPU local</li>
                <li><strong>Contención:</strong> código hostil contenido en el sandbox, host protegido</li>
            </ul>
        </div>
    </div>

    <script>
        async function runTask() {
            const framework = document.getElementById('framework').value;
            const circuit = document.getElementById('circuit').value.trim();
            const shots = parseInt(document.getElementById('shots').value) || 1024;
            const containment = document.getElementById('containment').checked;

            if (!circuit) {
                alert('Por favor ingresa una descripción del circuito');
                return;
            }

            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            statusDiv.style.display = 'block';
            resultDiv.style.display = 'none';

            document.getElementById('taskId').textContent = 'Enviando tarea...';
            document.getElementById('taskStatus').innerHTML = '<span class="badge badge-pending">PLANIFICANDO</span>';

            try {
                const resp = await fetch('/tasks', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        framework: framework,
                        circuit_description: circuit,
                        shots: shots,
                        containment_test: containment,
                    }),
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.detail || 'Error al crear tarea');
                }

                const data = await resp.json();
                document.getElementById('taskId').textContent = `Task ID: ${data.task_id}`;
                document.getElementById('taskStatus').innerHTML = `<span class="badge badge-pending">${data.status}</span>`;

                // Polling del estado
                let attempts = 0;
                const maxAttempts = 30;
                while (attempts < maxAttempts) {
                    await new Promise(r => setTimeout(r, 1000));
                    const st = await fetch(`/tasks/${data.task_id}`);
                    const stData = await st.json();
                    document.getElementById('taskStatus').innerHTML = `<span class="badge badge-pending">${stData.status}</span>`;

                    if (stData.status in ('completed', 'failed_execution', 'verified', 'result_ready')) {
                        break;
                    }
                    attempts++;
                }

                // Mostrar resultado
                const final = await fetch(`/tasks/${data.task_id}`);
                const finalData = await final.json();
                const res = finalData.result;

                resultDiv.style.display = 'block';
                let content = `Task ID: ${res.task_id}\n`;
                content += `Estado: ${res.status}\n`;
                content += `Framework: ${res.framework}\n`;
                content += `Contención activada: ${res.containment_triggered}\n`;
                content += `Sandbox destruido: ${res.sandbox_destroyed}\n`;
                content += `Tiempo de ejecución: ${res.execution_time_seconds ? res.execution_time_seconds.toFixed(2) : 'N/A'} s\n`;
                if (res.return_code !== undefined) content += `Código de salida: ${res.return_code}\n`;
                content += `\n--- Salida de ejecución ---\n`;
                content += res.execution_output || '(sin salida)';
                if (res.execution_error) content += `\n--- Errores ---\n${res.execution_error}`;
                if (res.generated_code) content += `\n\n--- Código generado ---\n${res.generated_code}`;

                document.getElementById('resultContent').textContent = content;

                const badgeClass = res.containment_triggered ? 'badge-fail' : (res.status === 'completed' ? 'badge-ok' : 'badge-fail');
                document.getElementById('taskStatus').innerHTML = `<span class="badge ${badgeClass}">${res.status}</span>`;

            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
    </script>
</body>
</html>
    """)