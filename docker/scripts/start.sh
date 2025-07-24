#!/bin/bash

# Script de inicialização para produção (Railway)
set -e

echo "🚀 Iniciando YouTube Download API em produção..."

# Executar migrações do banco de dados
echo "🗄️ Executando migrações..."
python run_migration.py

# Verificar se as migrações foram bem-sucedidas
if [ $? -ne 0 ]; then
    echo "⚠️ Aviso: Migrações falharam, mas continuando..."
fi

# Iniciar Nginx em background
echo "🌐 Iniciando Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Aguardar um pouco para o Nginx inicializar
sleep 2

# Iniciar a API FastAPI
echo "🔧 Iniciando API FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 