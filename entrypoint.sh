#!/bin/sh
set -e

echo "Esperando a PostgreSQL..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Cargando fixtures de eventos..."
python manage.py loaddata fixtures/seed_eventos.json || true

echo "Creando usuarios de prueba..."
python manage.py seed_usuarios || true

echo "Iniciando servidor ASGI (Daphne)..."
exec daphne -b 0.0.0.0 -p 8000 core.asgi:application
