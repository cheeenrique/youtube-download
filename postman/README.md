# 📋 Testes da YouTube Download API

Este diretório contém todos os arquivos necessários para testar a YouTube Download API usando o Postman.

## 📁 Arquivos Incluídos

### 1. `YouTube_Download_API.postman_collection.json`

Coleção completa do Postman com todos os endpoints organizados por funcionalidade:

- 🔐 Segurança (autenticação, validação, eventos)
- 📊 Monitoramento (métricas, health checks, alertas)
- 📥 Downloads (iniciar, listar, cancelar)
- ☁️ Google Drive (configuração, upload, quota)
- 🔗 URLs Temporárias (criar, acessar, revogar)
- 📈 Analytics (dashboard, estatísticas, relatórios)
- ⚡ Otimização (cache, performance, banco de dados)
- 🔧 Utilitários (health check, informações da API)

### 2. `YouTube_API_Environment.postman_environment.json`

Arquivo de ambiente do Postman com todas as variáveis necessárias:

- `base_url`: URL base da API
- `auth_token`: Token JWT de autenticação
- `download_id`: ID do download para testes
- `temp_url_id`: ID da URL temporária para testes
- Credenciais de teste e configurações opcionais

### 3. `test_api.py`

Script Python para testes automatizados da API:

- Testa todos os endpoints principais
- Gera relatório de testes
- Verifica funcionalidades básicas e avançadas
- Útil para CI/CD e testes rápidos

## 🚀 Como Usar

### Opção 1: Postman (Recomendado)

1. **Importar Coleção**:

   - Abra o Postman
   - Clique em "Import"
   - Selecione `YouTube_Download_API.postman_collection.json`

2. **Importar Ambiente**:

   - Clique em "Import" novamente
   - Selecione `YouTube_API_Environment.postman_environment.json`

3. **Configurar Ambiente**:

   - Selecione o ambiente "YouTube API Local"
   - Ajuste a variável `base_url` se necessário

4. **Seguir o Guia**:
   - Consulte `POSTMAN_TESTING_GUIDE.md` para instruções detalhadas

### Opção 2: Script Python

```bash
# Executar testes automatizados
python test_api.py

# Ou com URL personalizada
python test_api.py http://localhost:8000
```

## 📋 Checklist de Testes

### ✅ Pré-requisitos

- [ ] API rodando em `http://localhost:8000`
- [ ] Redis configurado e rodando
- [ ] PostgreSQL configurado e rodando
- [ ] Celery workers rodando
- [ ] Postman instalado (opcional)

### ✅ Testes Básicos

- [ ] Health check da API
- [ ] Informações da API
- [ ] Autenticação JWT
- [ ] Validação de entrada

### ✅ Testes de Funcionalidade

- [ ] Download de vídeos
- [ ] URLs temporárias
- [ ] Analytics e relatórios
- [ ] Monitoramento e alertas
- [ ] Otimização e cache

### ✅ Testes de Segurança

- [ ] Rate limiting
- [ ] Validação de entrada
- [ ] Logs de segurança
- [ ] Eventos de segurança

## 🔧 Configuração de Variáveis

### Variáveis Obrigatórias

```json
{
  "base_url": "http://localhost:8000",
  "auth_token": "",
  "download_id": "",
  "temp_url_id": ""
}
```

### Variáveis Opcionais

```json
{
  "user_id": "test_user",
  "password": "test_password",
  "test_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "test_email": "test@example.com",
  "admin_email": "admin@example.com"
}
```

### Variáveis para Notificações

```json
{
  "webhook_url": "https://your-webhook-url.com/alerts",
  "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
  "discord_webhook": "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK",
  "telegram_bot_token": "your-telegram-bot-token",
  "telegram_chat_id": "your-telegram-chat-id"
}
```

### Variáveis do Google Drive

```json
{
  "google_client_id": "your-client-id.apps.googleusercontent.com",
  "google_client_secret": "your-client-secret",
  "google_refresh_token": "your-refresh-token",
  "google_folder_id": "your-folder-id"
}
```

## 🧪 Cenários de Teste

### 1. Fluxo Básico

1. Gerar token de autenticação
2. Iniciar download de vídeo
3. Verificar progresso
4. Criar URL temporária
5. Acessar URL temporária

### 2. Teste de Segurança

1. Testar rate limiting
2. Validar entradas maliciosas
3. Verificar logs de segurança
4. Testar bloqueio de IPs

### 3. Teste de Monitoramento

1. Verificar métricas do sistema
2. Executar health checks
3. Configurar notificações
4. Gerar relatórios

### 4. Teste de Performance

1. Verificar status do cache
2. Analisar performance
3. Otimizar banco de dados
4. Testar compressão

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Conexão

```
❌ GET /health - Erro: Connection refused
```

**Solução**: Verificar se a API está rodando em `http://localhost:8000`

#### 2. Erro de Autenticação

```
❌ POST /security/token - Status: 401
```

**Solução**: Verificar se o banco de dados está configurado e acessível

#### 3. Erro de Redis

```
❌ GET /optimization/cache/status - Status: 500
```

**Solução**: Verificar se o Redis está rodando e acessível

#### 4. Erro de Celery

```
❌ POST /downloads/ - Status: 500
```

**Solução**: Verificar se os workers Celery estão rodando

### Verificações de Sistema

```bash
# Verificar se a API está rodando
curl http://localhost:8000/health

# Verificar se o Redis está rodando
redis-cli ping

# Verificar se o PostgreSQL está rodando
psql -h localhost -U postgres -c "SELECT 1;"

# Verificar workers Celery
celery -A app.infrastructure.celery.celery_app inspect active
```

## 📊 Relatórios

### Relatório do Script Python

O script `test_api.py` gera um arquivo `test_report.json` com:

- Timestamp dos testes
- Status da autenticação
- IDs de recursos criados
- Resumo dos testes executados

### Relatórios do Postman

O Postman pode gerar relatórios detalhados:

1. Clique em "View more actions" na coleção
2. Selecione "Export"
3. Escolha formato JSON ou HTML
4. Inclua relatórios de execução

## 🔄 Integração Contínua

### GitHub Actions

```yaml
name: API Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install requests
      - name: Run API tests
        run: python postman/test_api.py
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Test API') {
            steps {
                sh 'python postman/test_api.py'
            }
        }
    }
}
```

## 📞 Suporte

Para problemas com os testes:

1. Verifique os logs da API
2. Consulte o guia de troubleshooting
3. Verifique se todos os serviços estão rodando
4. Abra uma issue no repositório

---

**Boa sorte com os testes! 🚀**
