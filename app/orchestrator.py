from .models import (
    CircuitSpec,
    ExecutionPlan,
    PlanStep,
    TaskStatus,
    Framework,
)
import httpx
import os
from typing import Optional


VULTR_INFERENCE_URL = os.getenv("VULTR_INFERENCE_URL", "https://api.vultrinference.com/v1")
VULTR_API_KEY = os.getenv("VULTR_API_KEY", "")
VULTR_INFERENCE_MODEL = os.getenv("VULTR_INFERENCE_MODEL", "meta-llama/Llama-3.1-8B-Instruct")


class VultrInferenceClient:
    """Cliente para Vultr Serverless Inference (OpenAI-compatible)."""

    def __init__(self):
        self.base_url = VULTR_INFERENCE_URL.rstrip("/")
        self.api_key = VULTR_API_KEY
        self.model = VULTR_INFERENCE_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=30.0)
        return self._client

    async def chat_completion(self, messages: list, temperature: float = 0.3) -> str:
        """Envía mensajes al modelo de inferencia y devuelve la respuesta de texto."""
        client = await self._get_client()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        try:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            # Modo fallback para demo sin API real: devuelve un plan genérico
            return self._fallback_response(messages)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _fallback_response(self, messages: list) -> str:
        """Genera un plan de respaldo cuando no hay API de Vultr disponible."""
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content", "")
                break

        framework = "qiskit"
        for fw in ["qiskit", "pennylane", "cirq", "azure", "cpu_local"]:
            if fw in last_user.lower():
                framework = fw
                break

        steps = [
            PlanStep(step=1, action="analizar_especificacion", details=f"Analizar la especificación del usuario para framework {framework}"),
            PlanStep(step=2, action="generar_codigo", details=f"Generar código de prueba cuántica en {framework}"),
            PlanStep(step=3, action="levantar_sandbox", details="Levantar contenedor Docker aislado con límites de CPU/memoria/tiempo"),
            PlanStep(step=4, action="ejecutar_codigo", details="Ejecutar el código de prueba dentro del sandbox"),
            PlanStep(step=5, action="verificar_salida", details="Verificar que la salida es válida y que la contención se mantuvo"),
            PlanStep(step=6, action="destruir_sandbox", details="Destruir el contenedor tras la tarea (ciclo de vida)"),
        ]
        import json
        return json.dumps({
            "plan": [s.model_dump() for s in steps],
            "framework": framework,
            "estimated_time_seconds": 60,
            "fallback": True,
            "reason": "Vultr Inference API no disponible, usando plan predeterminado",
        })


_inference_client: Optional[VultrInferenceClient] = None


async def get_inference_client() -> VultrInferenceClient:
    global _inference_client
    if _inference_client is None:
        _inference_client = VultrInferenceClient()
    return _inference_client


async def plan_task(spec: CircuitSpec, task_id: str) -> ExecutionPlan:
    """Usa el LLM de Vultr para descomponer la tarea en pasos ejecutables."""
    client = await get_inference_client()

    system_prompt = (
        "Eres un orquestador de agentes cuánticos. Tu trabajo es descomponer una "
        "especificación de circuito cuántico en pasos ejecutables para un sandbox Docker. "
        "Responde SOLO con JSON válido. No incluyas texto adicional."
    )

    user_prompt = (
        f"Especificación del usuario:\n"
        f"- Framework: {spec.framework}\n"
        f"- Descripción del circuito: {spec.circuit_description}\n"
        f"- Shots: {spec.shots}\n"
        f"- Backend remoto: {spec.backend or 'ninguno (simulador local)'}\n"
        f"- Prueba de contención: {spec.containment_test}\n\n"
        f"Genera un plan con pasos numerados. Cada paso tiene: step (int), action (string), details (string). "
        f"Incluye: analizar_especificacion, generar_codigo, levantar_sandbox, ejecutar_codigo, verificar_salida, destruir_sandbox. "
        f"Devuelve JSON con claves: plan (lista de pasos), framework, estimated_time_seconds."
    )

    response = await client.chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    import json
    try:
        data = json.loads(response)
        steps = [PlanStep(**s) for s in data.get("plan", [])]
        framework = data.get("framework", spec.framework.value)
        estimated = data.get("estimated_time_seconds", 60)
    except Exception:
        # Fallback si el JSON no es válido
        steps = [
            PlanStep(step=1, action="analizar_especificacion", details="Analizar especificación"),
            PlanStep(step=2, action="generar_codigo", details="Generar código de prueba"),
            PlanStep(step=3, action="levantar_sandbox", details="Levantar sandbox Docker"),
            PlanStep(step=4, action="ejecutar_codigo", details="Ejecutar código"),
            PlanStep(step=5, action="verificar_salida", details="Verificar salida"),
            PlanStep(step=6, action="destruir_sandbox", details="Destruir sandbox"),
        ]
        framework = spec.framework.value
        estimated = 60

    plan = ExecutionPlan(
        task_id=task_id,
        steps=steps,
        framework=Framework(framework),
        estimated_time_seconds=estimated,
    )
    return plan


async def generate_code(spec: CircuitSpec, plan: ExecutionPlan) -> str:
    """Genera el código de prueba cuántica usando el LLM o una plantilla de fallback."""
    client = await get_inference_client()

    system_prompt = (
        "Eres un experto en computación cuántica. Genera código Python de prueba "
        "para el framework solicitado. El código debe ser autocontenido, imprimir "
        "resultados verificables y manejar errores. Responde SOLO con el código Python, "
        "sin markdown ni explicaciones adicionales."
    )

    user_prompt = (
        f"Framework: {spec.framework}\n"
        f"Descripción del circuito: {spec.circuit_description}\n"
        f"Shots: {spec.shots}\n"
        f"Backend: {spec.backend or 'simulador CPU local'}\n"
        f"Containment test: {spec.containment_test}\n\n"
        f"Genera un script Python completo que:\n"
        f"1. Importe el framework adecuado\n"
        f"2. Construya el circuito descrito\n"
        f"3. Ejecute la prueba con {spec.shots} shots\n"
        f"4. Imprima los resultados en formato legible\n"
        f"5. Si containment_test es True, incluya un bucle controlado que se detenga por límite de tiempo\n"
        f"Devuelve SOLO el código Python."
    )

    response = await client.chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    # Limpiar posibles bloques de markdown
    code = response.strip()
    if code.startswith("```python"):
        code = code[7:]
    if code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    # Si la respuesta es JSON del fallback (no código Python válido),
    # usar la plantilla de código predeterminada por framework.
    if code.startswith("{") and code.endswith("}"):
        try:
            import json as _json
            _json.loads(code)
            code = fallback_code(spec)
        except Exception:
            pass

    if not code:
        code = fallback_code(spec)

    return code.strip()


def fallback_code(spec: CircuitSpec) -> str:
    """Genera código de prueba predeterminado por framework cuando el LLM no está disponible."""
    fw = spec.framework.value
    shots = spec.shots
    containment = spec.containment_test

    if fw == "qiskit":
        return f'''from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import time

# Circuito generado por el agente: {spec.circuit_description}
qc = QuantumCircuit(3, 3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure([0, 1, 2], [0, 1, 2])

simulator = AerSimulator()
compiled = transpile(qc, simulator)
job = simulator.run(compiled, shots={shots})
result = job.result()
counts = result.get_counts(qc)

print("RESULTADO_QISKIT")
print(f"Shots: {shots}")
print(f"Conteos: {{counts}}")
print("ESTADO: completado")

{"import time; time.sleep(120)" if containment else "# Sin prueba de contención"}
'''

    elif fw == "pennylane":
        return f'''import pennylane as qml
from pennylane import numpy as np
import time

dev = qml.device("default.qubit", wires=3)

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])
    return qml.sample(qml.PauliZ(wires=[0, 1, 2]))

result = circuit()
shots = {shots}
unique, counts = np.unique(result, axis=0, return_counts=True)

print("RESULTADO_PENNYLANE")
print(f"Shots: {shots}")
print(f"Resultados: {{dict(zip([tuple(u) for u in unique], counts.tolist()))}}")
print("ESTADO: completado")

{"import time; time.sleep(120)" if containment else "# Sin prueba de contención"}
'''

    elif fw == "cirq":
        return f'''import cirq
import time

# Circuito generado por el agente: {spec.circuit_description}
qubits = cirq.LineQubit.range(3)
circuit = cirq.Circuit(
    cirq.H(qubits[0]),
    cirq.CNOT(qubits[0], qubits[1]),
    cirq.CNOT(qubits[1], qubits[2]),
    cirq.measure(*qubits, key="m"),
)

simulator = cirq.Simulator()
result = simulator.run(circuit, repetitions={shots})

print("RESULTADO_CIRQ")
print(f"Repeticiones: {{shots}}")
print(f"Histogramas: {{dict(result.histogram(key='m'))}}")
print("ESTADO: completado")

{"import time; time.sleep(120)" if containment else "# Sin prueba de contención"}
'''

    elif fw == "azure":
        return f'''# Adaptador Azure Quantum
# Requiere: pip install azure-quantum
from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider

print("RESULTADO_AZURE")
print("Framework: Azure Quantum")
print("Nota: Configure AZURE_QUANTUM_KEY y workspace para ejecución real")
print("Circuito: {{spec.circuit_description}}")
print("Shots: {{shots}}")
print("ESTADO: configurado (sin ejecución real sin credenciales)")

{"import time; time.sleep(120)" if containment else "# Sin prueba de contención"}
'''

    else:  # cpu_local
        return f'''# Simulador CPU local (fallback sin dependencias cuánticas)
import time
import json

# Simulación simplificada de un circuito de 3 qubits con Hadamard + CNOT
# Descripción: {spec.circuit_description}
shots = {shots}

# Estados posibles para 3 qubits
states = ["000", "001", "010", "011", "100", "101", "110", "111"]

# Distribución simulada (Hadamard en q0 crea superposición, CNOT entangle)
import random
random.seed(42)
counts = {{s: 0 for s in states}}
for _ in range(shots):
    # Simula medición: |000> y |111> son los más probables con entanglemento
    r = random.random()
    if r < 0.45:
        counts["000"] += 1
    elif r < 0.90:
        counts["111"] += 1
    else:
        remaining = [s for s in states if s not in ("000", "111")]
        counts[random.choice(remaining)] += 1

print("RESULTADO_CPU_LOCAL")
print(f"Framework: simulador CPU local")
print(f"Shots: {{shots}}")
print(f"Conteos: {{json.dumps(counts)}}")
print("ESTADO: completado")

{"import time; time.sleep(120)" if containment else "# Sin prueba de contención"}
'''


async def orchestrate(spec: CircuitSpec, task_id: str) -> str:
    """Orquesta la planificación y generación de código para una tarea."""
    from .store import store_plan, update_task_status, _tasks
    from .models import TaskStatus

    plan = await plan_task(spec, task_id)
    store_plan(task_id, plan)

    code = await generate_code(spec, plan)
    if not code:
        code = fallback_code(spec)

    task = _tasks.get(task_id)
    if task:
        task.generated_code = code
        task.status = TaskStatus.CODE_GENERATED

    return code
