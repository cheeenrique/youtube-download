# Guia de Deploy para Railway

## Visão Geral

Este guia explica como fazer o deploy da YouTube Download API no Railway, incluindo a API principal, Celery workers e banco de dados.

## 🚀 Deploy da API Principal

### 1. Preparação do Repositório

Certifique-se de que os seguintes arquivos estão no repositório:

- `Dockerfile.prod` - Dockerfile para produção
- `railway.json` - Configuração do Railway
- `requirements.txt` - Dependências Python
- `app/` - Código da aplicação
- `alembic/` - Migrações do banco

### 2. Conectar ao Railway

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Fazer login
railway login

# Inicializar projeto
railway init

# Conectar ao repositório
railway link
```

### 3. Configurar Variáveis de Ambiente

No painel do Railway, configure as seguintes variáveis:

#### Banco de Dados

```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

#### Celery

```bash
CELERY_BROKER_URL=sqla+postgresql://username:password@host:port/database
CELERY_RESULT_BACKEND=db+postgresql://username:password@host:port/database
```

#### Segurança

```bash
SECRET_KEY=your-super-secret-key-here
DEBUG=false
```

#### Downloads

```bash
MAX_CONCURRENT_DOWNLOADS=1
TEMP_FILE_EXPIRATION=3600
```

#### Google Drive (opcional)

```bash
GOOGLE_DRIVE_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_DRIVE_FOLDER_ID=your-folder-id
```

### 4. Deploy

```bash
# Fazer deploy
railway up

# Ver logs
railway logs

# Abrir no navegador
railway open
```

## 🔄 Deploy dos Workers Celery

### Opção 1: Múltiplos Projetos (Recomendado)

Crie projetos separados no Railway para cada serviço:

#### Projeto 1: API Principal

- Use `Dockerfile.prod`
- Configure como mostrado acima

#### Projeto 2: Celery Worker

- Use `Dockerfile.celery`
- Configure as mesmas variáveis de ambiente
- Conecte ao mesmo banco de dados

#### Projeto 3: Celery Beat

- Use `Dockerfile.celery-beat`
- Configure as mesmas variáveis de ambiente
- Conecte ao mesmo banco de dados

### Opção 2: Script de Inicialização

Crie um script que decide qual serviço rodar baseado em variável de ambiente:

```bash
#!/bin/bash
# start.sh

case $SERVICE_TYPE in
  "api")
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
    ;;
  "celery")
    celery -A app.infrastructure.celery.celery_app worker --loglevel=info
    ;;
  "celery-beat")
    celery -A app.infrastructure.celery.celery_app beat --loglevel=info
    ;;
  *)
    echo "SERVICE_TYPE não definido. Use: api, celery, ou celery-beat"
    exit 1
    ;;
esac
```

## 🗄️ Configuração do Banco de Dados

### 1. Adicionar Plugin PostgreSQL

No painel do Railway:

1. Vá para o projeto
2. Clique em "New Service"
3. Selecione "Database" → "PostgreSQL"
4. Configure as credenciais

### 2. Conectar Serviços

Após criar o banco:

1. Vá para o serviço da API
2. Clique em "Variables"
3. Adicione a variável `DATABASE_URL` com a URL fornecida pelo Railway

### 3. Executar Migrações

```bash
# Via Railway CLI
railway run alembic upgrade head

# Ou via painel do Railway
# Vá para o serviço → Deploy → Execute Command
alembic upgrade head
```

## 📁 Estrutura de Arquivos no Railway

### Arquivos Necessários

```
youtube-download-api/
├── Dockerfile.prod          # Para API principal
├── Dockerfile.celery        # Para Celery worker
├── Dockerfile.celery-beat   # Para Celery beat
├── railway.json             # Configuração Railway
├── requirements.txt         # Dependências Python
├── app/                     # Código da aplicação
├── alembic/                 # Migrações
└── alembic.ini             # Configuração Alembic
```

### Arquivos Ignorados

- `docker-compose.yml` (só para desenvolvimento local)
- `Dockerfile` (versão de desenvolvimento)
- `.env` (variáveis configuradas no Railway)
- `videos/` (criado automaticamente)
- `logs/` (criado automaticamente)

## 🔧 Configurações Avançadas

### Health Check

O Railway usa o endpoint `/health` para verificar se a aplicação está funcionando:

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### Porta Dinâmica

O Railway fornece a porta via variável `$PORT`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

### Logs

Os logs são automaticamente coletados pelo Railway:

- Acesse via painel do Railway
- Ou use `railway logs` no CLI

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Build Falha

```bash
# Verificar logs do build
railway logs --build

# Verificar se todas as dependências estão em requirements.txt
```

#### 2. Aplicação não Inicia

```bash
# Verificar logs
railway logs

# Verificar variáveis de ambiente
railway variables
```

#### 3. Banco não Conecta

```bash
# Verificar DATABASE_URL
railway variables

# Testar conexão
railway run python -c "from app.infrastructure.database.connection import get_db; print('DB OK')"
```

#### 4. Celery não Funciona

```bash
# Verificar CELERY_BROKER_URL
railway variables

# Verificar se o worker está rodando
railway logs --service celery
```

### Comandos Úteis

```bash
# Ver status dos serviços
railway status

# Ver variáveis de ambiente
railway variables

# Executar comando no container
railway run python manage.py shell

# Fazer deploy manual
railway up

# Ver logs em tempo real
railway logs --follow
```

## 📊 Monitoramento

### Métricas Disponíveis

- Uso de CPU e memória
- Logs de aplicação
- Status de health check
- Tempo de resposta

### Alertas

Configure alertas no painel do Railway para:

- Falhas de deploy
- Health check falhando
- Uso alto de recursos

## 🔄 CI/CD

### GitHub Actions (Opcional)

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: "16"
      - run: npm install -g @railway/cli
      - run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## 💰 Custos

### Railway Pricing

- **Hobby**: $5/mês por projeto
- **Pro**: $20/mês por projeto
- **Team**: $20/mês por usuário

### Otimizações de Custo

1. Use apenas um worker Celery
2. Configure auto-sleep para projetos não críticos
3. Monitore uso de recursos
4. Use storage externo para arquivos grandes

## 📞 Suporte

- [Documentação Railway](https://docs.railway.app/)
- [Discord Railway](https://discord.gg/railway)
- [GitHub Issues](https://github.com/railwayapp/railway/issues)
