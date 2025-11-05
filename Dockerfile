# ---- Etapa 1: Construcción de dependencias ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar paquetes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejora la caché)
COPY requirements.txt .

# Crear un entorno virtual para evitar conflictos
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ---- Etapa 2: Imagen final ----
FROM python:3.11-slim

# Establecer el entorno virtual por defecto
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar herramientas mínimas (solo lo necesario)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar el entorno virtual desde la etapa anterior
COPY --from=builder /opt/venv /opt/venv

# Copiar el código del proyecto
COPY . .

# Crear carpetas necesarias con permisos correctos
RUN mkdir -p logs && chmod 755 logs

# Exponer el puerto de Django/Gunicorn
EXPOSE 8000

# Instalar pandas adicionalmente
RUN pip install pandas

# Comando por defecto (production-ready)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]

