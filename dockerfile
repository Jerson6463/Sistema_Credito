# Usar una imagen oficial de Python ligera
FROM python:3.12-slim

# Evitar que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evitar que Python almacene en buffer el stdout y stderr
ENV PYTHONUNBUFFERED=1

# Configurar el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar ciertos paquetes (como psycopg2)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

# Copiar el archivo de requerimientos e instalarlos
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/