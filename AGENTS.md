# AGENTS.md — agent-rush

> Este archivo lo escribe una persona, no un generador. Empieza por lo que el agente
> no puede deducir del código. Si no sabes algo, déjalo vacío y no lo rellenes de
> suposiciones: un dato falso aquí contamina todo lo que el agente haga después.

## Qué es

Agente web que prueba circuitos y simulaciones cuánticas de forma aislada y verificable en Vultr, para el hackathon Vultr: Agent Rush (lablab.ai × Vultr, 3–8 nov 2026). Desafío: **Blast Radius Zero** — el agente planifica, despacha a un sandbox Docker y devuelve salida verificable, con contención obligatoria.

## Por qué este stack

- **Vultr Cloud Compute** como backend y capa de control/orquestación central (requerido por el evento).
- **Vultr Serverless Inference** (`https://api.vultrinference.com/v1`, OpenAI-compatible) para las llamadas LLM del agente (requerido; GPUs de Vultr no disponibles en este evento).
- **Docker** para aislamiento de ejecuciones cuánticas (requerido; contenedores desechables con límites de tiempo/memoria).
- Frameworks: Qiskit (IBM), PennyLane (AWS Braket), Cirq (Google), Azure Quantum (Microsoft); simulador CPU local como fallback (compatibilidad NVIDIA CUDA-Q / AMD ROCm).
- Todo desplegado en Vultr con URL pública de demo y vídeo de contención como entregables del jurado.

## Cómo arrancar

```bash
# instalar
cp .env.example .env   # rellenar VULTR_API_KEY, VULTR_INFERENCE_URL
pip install -r requirements.txt   # FastAPI, uvicorn, docker, qiskit, pennylane

# correr
uvicorn app.main:app --host 0.0.0.0 --port 8000   # backend en VM de Vultr
```

## Estructura

- `docs/C4.md` — modelo C4 (contexto, contenedores, componentes, despliegue)
- `docs/workflow.md` — diagrama de secuencia UML, flujo de estados, reglas de contención
- `docs/ADR/0001-quantum-testing-agent-architecture.md` — decisión de arquitectura (MADR reducido)
- `docs/demo-script.md` — guion de demo con momento de contención
- Detalle y bitácoras → vault: `02-PROYECTOS/2026-vultr-agent-rush/`

## Convenciones del equipo

- Trunk-based, sin Gitflow; ramas de vida < 4 h, squash merge a main.
- Conventional Commits: `feat(scope):`, `fix(scope):`, `docs:`, `test:`, `chore:`, `perf:`, `refactor:`.
- Sin `CHANGELOG.md`. Sin bitácoras en el repo.
- Containment-first: ningún código cuántico toca el host ni el backend.

## Lo que ya sabemos que falla

- El hackathon ya empezó (3 nov 2026) y cierra online el 8 nov 2026: quedan ~2 días.
- Vultr no tiene GPUs disponibles para este evento: toda la inferencia LLM pasa por Vultr Serverless Inference; las simulaciones cuánticas pesadas van a backends remotos (IBM/AWS/Azure) o al simulador CPU local.
- Sin vídeo de demo, URL pública ni repo público, Presentación se califica con 1 y tres de cuatro criterios se hunden.
- El simulador CPU es más lento que GPU; limitar el demo a circuitos pequeños (≤ 20 qubits).

## Alcance mínimo (MVP)

1. Endpoint REST `/tasks` que recibe especificación de circuito + framework.
2. Orquestador que usa Vultr Serverless Inference para planificar y generar código.
3. Sandbox Docker que ejecuta el código con límites y se destruye tras la tarea.
4. Resultado verificable devuelto a la UI web.
5. Vídeo de demo con momento de contención.
6. Repo público en GitHub y envío en lablab.ai.
