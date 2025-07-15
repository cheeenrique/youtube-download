#!/bin/bash

# Script de inicialização para Railway
# Define qual serviço rodar baseado na variável SERVICE_TYPE

echo "🚀 Iniciando serviço: $SERVICE_TYPE"

# Aguardar um pouco para o banco estar pronto
sleep 5

case $SERVICE_TYPE in
  "api")
    echo "📡 Iniciando API FastAPI..."
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
    ;;
  "celery")
    echo "🔄 Iniciando Celery Worker..."
    celery -A app.infrastructure.celery.celery_app worker --loglevel=info
    ;;
  "celery-beat")
    echo "⏰ Iniciando Celery Beat..."
    celery -A app.infrastructure.celery.celery_app beat --loglevel=info
    ;;
  *)
    echo "❌ SERVICE_TYPE não definido ou inválido: $SERVICE_TYPE"
    echo "Use: api, celery, ou celery-beat"
    echo "Iniciando API como padrão..."
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
    ;;
esac 