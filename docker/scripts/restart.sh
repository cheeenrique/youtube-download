#!/bin/bash

# Script para reiniciar o YouTube Download API
# Uso: ./docker/scripts/restart.sh

echo "🔄 Reiniciando YouTube Download API..."

# Parar serviços
echo "🛑 Parando serviços..."
docker-compose down

# Aguardar um pouco
sleep 2

# Iniciar serviços
echo "🚀 Iniciando serviços..."
docker-compose up -d

# Aguardar serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Verificar status
echo "📊 Status dos containers:"
docker-compose ps

echo "✅ YouTube Download API reiniciado com sucesso!" 