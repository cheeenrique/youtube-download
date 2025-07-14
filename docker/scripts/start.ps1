# Script PowerShell para iniciar o YouTube Download API com Docker
# Uso: .\docker\scripts\start.ps1

Write-Host "🚀 Iniciando YouTube Download API..." -ForegroundColor Green

# Verificar se o Docker está rodando
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker não está rodando. Por favor, inicie o Docker primeiro." -ForegroundColor Red
    exit 1
}

# Verificar se o docker-compose está disponível
try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "❌ docker-compose não está instalado." -ForegroundColor Red
    exit 1
}

# Criar diretórios necessários
Write-Host "📁 Criando diretórios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "videos\permanent" | Out-Null
New-Item -ItemType Directory -Force -Path "videos\temporary" | Out-Null
New-Item -ItemType Directory -Force -Path "videos\temp" | Out-Null
New-Item -ItemType Directory -Force -Path "logs\nginx" | Out-Null

# Construir e iniciar os containers
Write-Host "🔨 Construindo containers..." -ForegroundColor Yellow
docker-compose build

Write-Host "🚀 Iniciando serviços..." -ForegroundColor Yellow
docker-compose up -d

# Aguardar os serviços ficarem prontos
Write-Host "⏳ Aguardando serviços ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar status dos containers
Write-Host "📊 Status dos containers:" -ForegroundColor Yellow
docker-compose ps

# Verificar health checks
Write-Host "🏥 Verificando health checks..." -ForegroundColor Yellow
$services = @("api", "db", "redis", "celery")
foreach ($service in $services) {
    $status = docker-compose ps | Select-String $service
    if ($status -match "Up") {
        Write-Host "✅ $service está rodando" -ForegroundColor Green
    } else {
        Write-Host "❌ $service não está rodando corretamente" -ForegroundColor Red
    }
}

# Executar migrações
Write-Host "🗄️ Executando migrações do banco de dados..." -ForegroundColor Yellow
docker-compose exec api alembic upgrade head

Write-Host "🎉 YouTube Download API iniciado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 URLs disponíveis:" -ForegroundColor Cyan
Write-Host "   🌐 API: http://localhost" -ForegroundColor White
Write-Host "   📚 Documentação: http://localhost/api/docs" -ForegroundColor White
Write-Host "   🔌 WebSocket: ws://localhost/ws/dashboard" -ForegroundColor White
Write-Host "   📺 SSE: http://localhost/downloads/dashboard/stream" -ForegroundColor White
Write-Host ""
Write-Host "📝 Logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f api" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Para parar: docker-compose down" -ForegroundColor Yellow 