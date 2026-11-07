# ADR-0001 — Arquitectura del agente de pruebas cuánticas

## Contexto

El proyecto participa en el **Vultr: Agent Rush Hackathon** (lablab.ai × Vultr, 3–8 nov 2026). El desafío es **Blast Radius Zero**: un agente web que ejecute trabajo real (código cuántico) dentro de un sandbox aislado en Vultr, con salida verificable y contención obligatoria.

Requisitos del evento:
- Backend en VM de Vultr como capa de control y orquestación.
- Llamadas LLM obligatorias a **Vultr Serverless Inference** (`https://api.vultrinference.com/v1`, OpenAI-compatible).
- **GPUs de Vultr no disponibles** en este evento.
- Sandbox aislado: Docker recomendado; límites de tiempo/memoria; destroy tras cada tarea.
- No API keys ni credenciales dentro del sandbox.
- Entregables: repo público GitHub, backend desplegado en Vultr, URL pública de demo, vídeo con momento de contención, envío en lablab.ai.

El agente debe probar circuitos y simulaciones cuánticas bajo múltiples frameworks (Qiskit/IBM, PennyLane/AWS Braket, Cirq/Google, Azure Quantum/Microsoft) y hardware (NVIDIA CUDA-Q, AMD ROCm, simuladores CPU).

## Alternativas

| Alternativa | Descripción | Ventajas | Desventajas |
|---|---|---|---|
| A1 | Ejecutar simulaciones cuánticas localmente en la VM Vultr (CPU) con Qiskit/PennyLane puros | Sin dependencias externas, costo cero, control total | Limitado a CPU de la VM (Athlon-equivalente en la nube), no aprovecha hardware cuántico real, no demuestra compatibilidad multi-nube |
| A2 | Despachar trabajos a backends remotos (IBM Quantum, AWS Braket, Azure Quantum) vía sus APIs | Demuestra compatibilidad real con plataformas nube, hardware cuántico real disponible | Requiere API keys gestionadas en backend, latencia de red, posibles colas de espera, costos externos |
| A3 | Híbrido: simulador CPU local como fallback + backends remotos como destino principal | Mejor de ambos: demo funciona sin depender de colas externas, y demuestra compatibilidad multi-nube | Mayor complejidad de adaptadores y de orquestación |
| A4 | Usar GPUs locales (NVIDIA/AMD) para simulación | Aprovecha aceleración de hardware | **Inviable:** Vultr no tiene GPUs en este evento; la máquina local del usuario (Athlon 3000G Vega 3) no soporta ROCm para cómputo cuántico serio |

## Decisión

Se adopta la **alternativa A3 (híbrida)**:

- El orquestador genera código de prueba en el framework elegido (Qiskit, PennyLane, Cirq, Azure Quantum).
- El sandbox ejecuta el código. Por defecto usa **simulador CPU local** (statevector puro o CUDA-Q/ROCm cuando esté disponible) para garantizar que el demo funcione sin depender de colas externas.
- Se incluyen adaptadores para **IBM Quantum, AWS Braket y Azure Quantum** como backends remotos opcionales, configurables vía variables de entorno del backend (no del sandbox).
- Toda la inferencia del agente (planificación, generación de código, explicación) usa **Vultr Serverless Inference**.
- El sandbox es un contenedor Docker desechable con límites de CPU/memoria/tiempo, destruido tras cada tarea.
- Las credenciales de backends remotos viven solo en el backend de Vultr (variables de entorno), nunca dentro del sandbox.

## Consecuencias

### Positivas
- Demo robusto: no depende de disponibilidad ni colas de backends cuánticos externos.
- Cumple estrictamente los requisitos del hackathon (Vultr VM, Vultr Inference, Docker sandbox, contención, sin GPUs).
- Demuestra compatibilidad multi-framework y multi-nube mediante adaptadores configurables.
- Contención verificada: fallos en el circuito no afectan al host ni al backend.

### Negativas / riesgos
- El simulador CPU es más lento que GPU para circuitos grandes; se limitará a circuitos pequeños (≤ 20 qubits) en el demo.
- Los backends remotos requieren credenciales válidas del usuario/juez; si no se proveen, el demo se limita a simulador local.
- Complejidad adicional de mantener adaptadores por framework.

### Decisiones pendientes
- Qué frameworks incluir en el MVP (Qiskit + PennyLane como mínimo; Cirq y Azure como stretch).
- Cuota de tiempo por sandbox (propuesta: 60 s).
- Imagen base de Docker (slim de Python con Qiskit/PennyLane instalados).

---

**Tags:** #adr #arquitectura #quantum #hackaton #vultr #decision
