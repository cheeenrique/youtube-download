#!/bin/bash

# Script de inicialização para produção no Railway
# Executa migrações automaticamente e depois inicia a API

echo "🚀 Iniciando aplicação em produção..."

# Aguardar um pouco para o banco estar pronto
echo "⏳ Aguardando banco de dados..."
sleep 10

# Executar migrações
echo "🔄 Executando migrações..."
python run_migration.py

# Verificar se as migrações foram executadas com sucesso
if [ $? -eq 0 ]; then
    echo "✅ Migrações executadas com sucesso!"
else
    echo "❌ Erro ao executar migrações. Continuando mesmo assim..."
fi

# Iniciar a API
echo "📡 Iniciando API FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 