# ==========================================
# ETAPA 1: Builder (Compilación de dependencias)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Variables de entorno para que Python no genere .pyc y logs inmediatos
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema necesarias para compilar (gcc, libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
# Asegurar que usamos el pip del entorno virtual
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# ETAPA 2: Runner (Imagen Final Ligera)
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Instalar solo las librerías runtime necesarias (libpq para Postgres, client para debug)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar el entorno virtual compilado desde la etapa anterior
COPY --from=builder /opt/venv /opt/venv

# Copiar el código fuente
COPY . .

# Crear carpeta de logs y media con permisos
RUN mkdir -p logs media staticfiles && \
    chmod -R 755 logs media staticfiles

# Exponer puerto
EXPOSE 8000

# Comando por defecto (Gunicorn para producción)
# En desarrollo, docker-compose sobreescribe esto.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]