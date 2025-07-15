# Endpoint de Migrações Temporário

## ⚠️ ATENÇÃO

Este endpoint é **TEMPORÁRIO** e deve ser **REMOVIDO** antes de ir para produção!

## Propósito

Este endpoint foi criado para facilitar a execução de migrações Alembic no Railway, onde não há acesso direto ao terminal para executar comandos.

## Endpoints Disponíveis

### 1. Executar Migrações

```http
POST /migrate
```

**Descrição:** Executa todas as migrações pendentes até a versão mais recente.

**Resposta de Sucesso:**

```json
{
  "success": true,
  "message": "Migrações executadas com sucesso",
  "stdout": "...",
  "stderr": "..."
}
```

**Resposta de Erro:**

```json
{
  "detail": "Erro ao executar migrações: [mensagem de erro]"
}
```

### 2. Marcar Migrações como Aplicadas

```http
POST /migrate/stamp
```

**Descrição:** Marca as migrações como aplicadas sem executá-las. Útil quando o banco já tem a estrutura mas o Alembic não sabe.

**Resposta de Sucesso:**

```json
{
  "success": true,
  "message": "Migrações marcadas como aplicadas com sucesso",
  "stdout": "...",
  "stderr": "..."
}
```

**Resposta de Erro:**

```json
{
  "detail": "Erro ao marcar migrações: [mensagem de erro]"
}
```

### 3. Verificar Status das Migrações

```http
GET /migrate/status
```

**Descrição:** Verifica qual é a revisão atual do banco de dados.

**Resposta:**

```json
{
  "success": true,
  "current_revision": "80a50e7ad5f9",
  "stdout": "80a50e7ad5f9",
  "stderr": ""
}
```

### 4. Verificar Histórico de Migrações

```http
GET /migrate/history
```

**Descrição:** Mostra o histórico completo de migrações.

**Resposta:**

```json
{
  "success": true,
  "history": "001_initial_migration -> 002_add_temp_url_fields -> 003_add_download_logs_table -> 80a50e7ad5f9_add_users_table",
  "stdout": "...",
  "stderr": ""
}
```

## Como Usar

### 1. Via Postman

1. Abra o Postman
2. Crie uma nova requisição POST
3. URL: `https://seu-dominio-railway.up.railway.app/migrate`
4. Clique em "Send"

### 2. Via cURL

```bash
# Executar migrações
curl -X POST https://seu-dominio-railway.up.railway.app/migrate

# Marcar migrações como aplicadas (quando tabelas já existem)
curl -X POST https://seu-dominio-railway.up.railway.app/migrate/stamp
```

### 3. Via Navegador (apenas para GET)

```
https://seu-dominio-railway.up.railway.app/migrate/status
https://seu-dominio-railway.up.railway.app/migrate/history
```

## Fluxo de Trabalho Recomendado

1. **Antes de fazer deploy:**

   - Execute `alembic revision --autogenerate -m "descrição da migração"`
   - Teste localmente com `alembic upgrade head`

2. **Após fazer deploy no Railway:**

   - Acesse o endpoint `/migrate` para executar as migrações
   - Verifique o status com `/migrate/status`
   - Se necessário, verifique o histórico com `/migrate/history`

3. **Após confirmar que tudo está funcionando:**
   - **REMOVA** este endpoint antes de ir para produção!

## Logs

Todos os comandos de migração são logados no console da aplicação. Você pode verificar os logs no Railway para debug.

## Segurança

⚠️ **IMPORTANTE:** Este endpoint não tem autenticação e pode ser acessado por qualquer pessoa. Use apenas em ambiente de desenvolvimento/staging.

## Remoção do Endpoint

Para remover este endpoint:

1. Delete o arquivo `app/presentation/api/v1/migrations.py`
2. Remova a linha de import no `router.py`:
   ```python
   from .migrations import router as migrations_router
   ```
3. Remova a linha de inclusão no `router.py`:
   ```python
   api_router.include_router(migrations_router, tags=["Migrations"])
   ```
4. Remova a seção "migrations" do endpoint raiz

## Troubleshooting

### Erro: "alembic command not found"

- Verifique se o Alembic está instalado no `requirements.txt`
- Reinicie o container após adicionar a dependência

### Erro: "Database connection failed"

- Verifique se as variáveis de ambiente do banco estão corretas
- Confirme se o banco PostgreSQL está acessível

### Erro: "Permission denied"

- Verifique se o usuário do banco tem permissões para criar/modificar tabelas
- Confirme se a string de conexão está correta

### Erro: "relation already exists" ou "DuplicateTable"

- Este erro ocorre quando o banco já tem as tabelas mas o Alembic não sabe
- Use o endpoint `/migrate/stamp` para marcar as migrações como aplicadas sem executá-las
- Depois use `/migrate/status` para verificar se funcionou
