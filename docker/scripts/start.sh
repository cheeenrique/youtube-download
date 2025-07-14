#!/bin/bash

# Script para iniciar o YouTube Download API com Docker
# Uso: ./docker/scripts/start.sh

set -e

echo "🚀 Iniciando YouTube Download API..."

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker primeiro."
    exit 1
fi

# Verificar se o docker-compose está disponível
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose não está instalado."
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p videos/permanent videos/temporary videos/temp logs/nginx

# Definir permissões (Linux/Mac)
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    chmod -R 755 videos logs
fi

# Construir e iniciar os containers
echo "🔨 Construindo containers..."
docker-compose build

echo "🚀 Iniciando serviços..."
docker-compose up -d

# Aguardar os serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose ps

# Verificar health checks
echo "🏥 Verificando health checks..."
for service in api db redis celery; do
    if docker-compose ps | grep -q "$service.*Up"; then
        echo "✅ $service está rodando"
    else
        echo "❌ $service não está rodando corretamente"
    fi
done

# Executar migrações
echo "🗄️ Executando migrações do banco de dados..."
docker-compose exec api alembic upgrade head

echo "🎉 YouTube Download API iniciado com sucesso!"
echo ""
echo "📋 URLs disponíveis:"
echo "   🌐 API: http://localhost"
echo "   📚 Documentação: http://localhost/api/docs"
echo "   🔌 WebSocket: ws://localhost/ws/dashboard"
echo "   📺 SSE: http://localhost/downloads/dashboard/stream"
echo ""
echo "📝 Logs:"
echo "   docker-compose logs -f api"
echo ""
echo "🛑 Para parar: docker-compose down" 