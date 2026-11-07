# Demo script — Quantum Testing Agent

## Objetivo de la demo

Mostrar un agente web que prueba circuitos cuánticos de forma aislada y verificable en Vultr, cumpliendo el desafío **Blast Radius Zero** del hackathon. La demo debe incluir un **momento de contención** (sandbox absorbiendo un fallo sin comprometer el sistema).

## Duración

≤ 5 minutos (requerido por el jurado; por debajo de 3 min puntúa peor).

## Guion paso a paso

| # | Paso | Qué se muestra | Tiempo aprox. |
|---|---|---|---|
| 1 | **Apertura** | Presentar el problema: probar circuitos cuánticos es riesgoso (código arbitrario, bucles infinitos, comandos destructivos). Explicar que el agente aísla todo en un sandbox en Vultr. | 30 s |
| 2 | **Entrada de especificación** | El usuario escribe en la web: "Crea un circuito de 3 qubits con Hadamard y CNOT, mide en base Z, ejecuta 1024 shots en Qiskit". | 30 s |
| 3 | **Planificación del agente** | El agente (Vultr Serverless Inference) descompone la tarea en pasos: generar código Qiskit, validar sintaxis, ejecutar en sandbox, verificar resultados. Se muestra el plan en pantalla. | 30 s |
| 4 | **Generación de código** | El agente genera el script Python de prueba (Qiskit) y lo muestra brevemente. | 20 s |
| 5 | **Ejecución aislada** | Se levanta un contenedor Docker desechable en la VM de Vultr con límites (60 s, 512 MB). El código corre dentro del sandbox, aislado del host y del backend. | 45 s |
| 6 | **Resultado verificable** | El sandbox devuelve los estados de medida y histogramas. La web los muestra como resultado verificable (código de salida, logs, salida stdout). | 30 s |
| 7 | **Momento de contención (clave)** | El usuario envía un circuito hostil: un bucle infinito o un comando tipo `rm -rf` embebido. El sandbox lo detecta, mata el contenedor por límite de tiempo/recursos y destruye el entorno. El backend y el host permanecen intactos. Se muestra el mensaje "Contenido: entorno destruido, host seguro". | 60 s |
| 8 | **Compatibilidad multi-framework** | Se selecciona otro framework (PennyLane o Cirq) y se repite brevemente la prueba para demostrar que el agente es agnóstico al framework. | 30 s |
| 9 | **Cierre y arquitectura** | Resumen: backend en VM Vultr, LLM vía Vultr Serverless Inference, sandbox Docker, sin GPUs de Vultr (simulador CPU / backends remotos opcionales). Llamada a acción: repo GitHub público y URL de demo. | 45 s |

**Total estimado: ~4 min 30 s.**

## Momento de contención — detalle para el vídeo

- **Entrada hostil:** código que incluya `while True: pass` o `import os; os.system("rm -rf /tmp/test")`.
- **Comportamiento esperado:** el contenedor alcanza el límite de tiempo o memoria, Docker lo mata, el entorno se destruye, la API responde con `containment: true` y el mensaje "Entorno aislado destruido; host y backend sin afectar".
- **Evidencia en vídeo:** mostrar la terminal del backend registrando la destrucción del contenedor y la web mostrando el estado seguro.

## Requisitos técnicos para la demo

| Requisito | Detalle |
|---|---|
| Backend desplegado | VM de Vultr con FastAPI + Docker, accesible por URL pública |
| LLM | Vultr Serverless Inference (`https://api.vultrinference.com/v1`) |
| Frameworks instalados en imagen Docker | Qiskit, PennyLane (Cirq y Azure como opcionales) |
| Límites de sandbox | 60 s de CPU, 512 MB de memoria, red desactivada dentro del contenedor |
| Repo público | GitHub con README, setup, documentación y este guion de demo |
| Vídeo | ≤ 5 min, MP4, ≤ 300 MB, incluye momento de contención |

## Guion de voz (sugerido)

> "Hola, soy el agente de pruebas cuánticas. Este es un circuito de 3 qubits con Hadamard y CNOT. Lo voy a ejecutar de forma aislada en un sandbox de Docker en Vultr. El agente planificó la prueba, generó el código en Qiskit y lo ejecutó dentro del contenedor. Aquí está el resultado verificable: estados de medida y histogramas.
>
> Ahora voy a probar algo peligroso: un bucle infinito embebido en el circuito. Observen: el sandbox lo detecta, alcanza el límite de tiempo, destruye el contenedor y el sistema sigue intacto. Eso es contención.
>
> Todo corre en una VM de Vultr, con llamadas LLM a Vultr Serverless Inference, sin GPUs de Vultr, usando simulador CPU y backends remotos opcionales de IBM, AWS y Azure."

---

**Tags:** #demo #guion #contencion #quantum #hackaton #vultr
