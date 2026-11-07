from docker import APIClient
import os

# Imagen base para el sandbox de ejecución cuántica
FROM python:3.11-slim

# Evitar archivos .pyc y buffers de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar frameworks cuánticos (opcionales, para ejecución real)
# Descomentar según el framework necesario:
# RUN pip install --no-cache-dir qiskit qiskit-aer
# RUN pip install --no-cache-dir pennylane
# RUN pip install --no-cache-dir cirq

# Copiar el código de la aplicación (solo para referencia, el sandbox ejecuta código inyectado)
COPY app ./app

# Puerto de la API (para salud, aunque el sandbox ejecuta código aislado)
EXPOSE 8000

# Comando por defecto (no se usa directamente; el orquestador levanta contenedores por tarea)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
