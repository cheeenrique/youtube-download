#!/bin/bash

# Script para visualizar logs do YouTube Download API
# Uso: ./docker/scripts/logs.sh [service]

SERVICE=${1:-api}

echo "📝 Visualizando logs do serviço: $SERVICE"

case $SERVICE in
    "api")
        docker-compose logs -f api
        ;;
    "db")
        docker-compose logs -f db
        ;;
    "celery")
        docker-compose logs -f celery
        ;;
    "celery-beat")
        docker-compose logs -f celery-beat
        ;;
    "nginx")
        docker-compose logs -f nginx
        ;;
    "all")
        docker-compose logs -f
        ;;
    *)
        echo "❌ Serviço '$SERVICE' não encontrado."
        echo "📋 Serviços disponíveis:"
        echo "   api, db, celery, celery-beat, nginx, all"
        exit 1
        ;;
esac 