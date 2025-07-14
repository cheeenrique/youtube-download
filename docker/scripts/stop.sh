#!/bin/bash

# Script para parar o YouTube Download API
# Uso: ./docker/scripts/stop.sh

echo "🛑 Parando YouTube Download API..."

# Parar todos os containers
docker-compose down

echo "✅ Serviços parados com sucesso!"

# Opcional: remover volumes (descomente se quiser limpar dados)
# echo "🗑️ Removendo volumes..."
# docker-compose down -v

# Opcional: remover imagens (descomente se quiser limpar imagens)
# echo "🗑️ Removendo imagens..."
# docker-compose down --rmi all

echo "🎉 YouTube Download API parado!" 