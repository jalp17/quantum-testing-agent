Quantum Testing Agent — Vultr Agent Rush Hackathon

Backend FastAPI que recibe especificaciones de circuitos cuánticos,
las ejecuta en sandboxes Docker aislados en Vultr y devuelve
resultados verificables con contención obligatoria.

Stack: Python 3.11, FastAPI, uvicorn, docker, httpx, pydantic.
Frameworks soportados: Qiskit (IBM), PennyLane (AWS Braket), Cirq (Google),
Azure Quantum (Microsoft), simulador CPU local (fallback).
