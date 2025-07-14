# Deploy no Render - YouTube Download API

## Pré-requisitos

- Conta no [Render.com](https://render.com/)
- Projeto no GitHub/GitLab
- Docker Compose funcionando localmente

## Passos para Deploy

### 1. Preparar o Repositório

Certifique-se de que seu repositório contém:

- `render.yaml` (configuração do Render)
- `requirements.txt` (dependências Python)
- `Dockerfile` (se usar Docker)
- `alembic/` (migrações do banco)

### 2. Criar Conta no Render

1. Acesse [render.com](https://render.com/)
2. Crie uma conta (pode usar GitHub)
3. Verifique o email

### 3. Deploy via Blueprint

1. No dashboard do Render, clique em "New +"
2. Selecione "Blueprint"
3. Conecte seu repositório GitHub/GitLab
4. O Render detectará automaticamente o `render.yaml`
5. Clique em "Apply"

### 4. Configurar Variáveis de Ambiente

O Render configurará automaticamente:

- `DATABASE_URL` (conectado ao PostgreSQL do Render)
- `SECRET_KEY` (gerado automaticamente)

### 5. Aguardar o Deploy

- O Render fará build e deploy dos serviços
- API: ~5-10 minutos
- Worker: ~3-5 minutos
- Database: ~2-3 minutos

### 6. Executar Migrações

Após o deploy, execute as migrações:

```bash
# Via Render Shell ou conectando ao container
alembic upgrade head
```

### 7. Testar a API

- API: `https://seu-app.onrender.com`
- Docs: `https://seu-app.onrender.com/docs`
- Health: `https://seu-app.onrender.com/health`

## Estrutura do Deploy

### Serviços Criados:

1. **Web Service** (`youtube-download-api`)

   - Porta: 8000
   - Health Check: `/health`
   - Auto-deploy: Sim

2. **Worker** (`youtube-download-celery`)

   - Processa tarefas em background
   - Conectado ao mesmo banco
   - Auto-deploy: Sim

3. **Database** (`youtube-downloads-db`)
   - PostgreSQL 15
   - 1GB de storage (free tier)
   - Backup automático

## Limitações do Free Tier

### Recursos:

- **Web Service**: 750h/mês, 512MB RAM
- **Worker**: 750h/mês, 512MB RAM
- **Database**: 1GB storage, 90 dias de backup

### Comportamento:

- Serviços podem "dormir" se não acessados
- Primeiro acesso pode ser lento (cold start)
- Rate limiting aplicado

## Monitoramento

### Logs:

- Acesse os logs via dashboard do Render
- Logs em tempo real disponíveis
- Histórico de 7 dias (free tier)

### Métricas:

- CPU, Memory, Disk usage
- Request count, response time
- Error rates

## Troubleshooting

### Problemas Comuns:

1. **Build falha**

   - Verifique `requirements.txt`
   - Confirme versões Python
   - Verifique dependências

2. **Database connection error**

   - Aguarde database estar pronto
   - Verifique `DATABASE_URL`
   - Execute migrações

3. **Celery não funciona**

   - Verifique logs do worker
   - Confirme configuração PostgreSQL
   - Teste conexão manual

4. **Cold start lento**
   - Normal no free tier
   - Considere upgrade para paid plan
   - Implemente health checks

### Comandos Úteis:

```bash
# Ver logs
render logs

# Conectar ao container
render shell

# Executar migrações
alembic upgrade head

# Testar conexão
python -c "from app.infrastructure.database import check_db_connection; check_db_connection()"
```

## Upgrade para Paid Plan

Quando precisar de mais recursos:

1. **Web Service**: $7/mês (512MB RAM, sempre on)
2. **Worker**: $7/mês (512MB RAM, sempre on)
3. **Database**: $7/mês (1GB RAM, 10GB storage)

## URLs Importantes

- **Dashboard**: https://dashboard.render.com
- **Documentação**: https://render.com/docs
- **Status**: https://status.render.com
