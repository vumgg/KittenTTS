#!/bin/bash
# Entrypoint script for KittenTTS Docker container

set -e

echo "Starting KittenTTS Web Interface..."
echo "Port: ${PORT:-5000}"

# Run production WSGI server
exec gunicorn \
	--bind 0.0.0.0:${PORT:-5000} \
	--workers ${WEB_CONCURRENCY:-1} \
	--threads ${GUNICORN_THREADS:-2} \
	--timeout ${GUNICORN_TIMEOUT:-120} \
	app:app
