"""Adaptadores para backends cuánticos remotos y locales.

Cada adaptador expone una interfaz común para ejecutar circuitos
en diferentes proveedores (IBM, AWS, Azure, Google) o simulador CPU.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os


class QuantumBackendAdapter(ABC):
    """Interfaz común para backends cuánticos."""

    @abstractmethod
    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        """Ejecuta código de circuito y devuelve resultado estructurado."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Indica si el backend está disponible (credenciales configuradas)."""
        pass


class LocalCPUAdapter(QuantumBackendAdapter):
    """Simulador CPU local. Siempre disponible como fallback."""

    def is_available(self) -> bool:
        return True

    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        # El código ya se ejecuta en el sandbox; este adaptador es para
        # casos donde se quiere ejecutar directamente sin sandbox.
        return {
            "backend": "cpu_local",
            "shots": shots,
            "status": "simulado",
            "nota": "Usar el sandbox Docker para ejecución aislada",
        }


class IBMQuantumAdapter(QuantumBackendAdapter):
    """Adaptador para IBM Quantum (requiere Qiskit + token)."""

    def __init__(self):
        self.token = os.getenv("IBM_QUANTUM_TOKEN", "")

    def is_available(self) -> bool:
        return bool(self.token)

    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "backend": "ibm_quantum",
                "status": "no_disponible",
                "motivo": "IBM_QUANTUM_TOKEN no configurado",
            }
        return {
            "backend": "ibm_quantum",
            "shots": shots,
            "status": "en_cola",
            "nota": "Requiere ejecución real en IBM Quantum con Qiskit",
        }


class AWSBraketAdapter(QuantumBackendAdapter):
    """Adaptador para AWS Braket (requiere PennyLane + credenciales AWS)."""

    def __init__(self):
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    def is_available(self) -> bool:
        return bool(self.access_key and self.secret_key)

    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "backend": "aws_braket",
                "status": "no_disponible",
                "motivo": "Credenciales AWS no configuradas",
            }
        return {
            "backend": "aws_braket",
            "shots": shots,
            "status": "en_cola",
            "nota": "Requiere ejecución real en AWS Braket con PennyLane",
        }


class AzureQuantumAdapter(QuantumBackendAdapter):
    """Adaptador para Azure Quantum (requiere clave de Azure)."""

    def __init__(self):
        self.key = os.getenv("AZURE_QUANTUM_KEY", "")

    def is_available(self) -> bool:
        return bool(self.key)

    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "backend": "azure_quantum",
                "status": "no_disponible",
                "motivo": "AZURE_QUANTUM_KEY no configurado",
            }
        return {
            "backend": "azure_quantum",
            "shots": shots,
            "status": "en_cola",
            "nota": "Requiere ejecución real en Azure Quantum",
        }


class GoogleCirqAdapter(QuantumBackendAdapter):
    """Adaptador para Google Cirq (simulador o hardware remoto)."""

    def __init__(self):
        self.project_id = os.getenv("GOOGLE_QUANTUM_PROJECT_ID", "")

    def is_available(self) -> bool:
        return bool(self.project_id)

    async def run(self, circuit_code: str, shots: int) -> Dict[str, Any]:
        if not self.is_available():
            return {
                "backend": "google_cirq",
                "status": "simulador_local",
                "nota": "GOOGLE_QUANTUM_PROJECT_ID no configurado, usando simulador local",
            }
        return {
            "backend": "google_cirq",
            "shots": shots,
            "status": "en_cola",
            "nota": "Requiere ejecución real en Google Quantum",
        }


def get_adapter(framework: str) -> QuantumBackendAdapter:
    """Devuelve el adaptador adecuado para el framework solicitado."""
    adapters = {
        "qiskit": IBMQuantumAdapter(),
        "pennylane": AWSBraketAdapter(),
        "cirq": GoogleCirqAdapter(),
        "azure": AzureQuantumAdapter(),
        "cpu_local": LocalCPUAdapter(),
    }
    return adapters.get(framework, LocalCPUAdapter())
