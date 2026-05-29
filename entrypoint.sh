#!/bin/sh
set -e

echo "Esperando a PostgreSQL..."
until python -c "
import socket, sys
try:
    s = socket.create_connection(('$DB_HOST', int('$DB_PORT')), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  DB no disponible, reintentando..."
  sleep 2
done
echo "PostgreSQL listo."

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Cargando fixtures de eventos..."
python manage.py loaddata fixtures/seed_eventos.json || true

echo "Creando usuarios de prueba..."
python manage.py seed_usuarios || true

echo "Iniciando servidor ASGI (Daphne)..."
exec daphne -b 0.0.0.0 -p 8000 core.asgi:application
