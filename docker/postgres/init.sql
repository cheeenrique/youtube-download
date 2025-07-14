-- Script de inicialização do PostgreSQL para YouTube Download API
-- Este script é executado automaticamente quando o container é criado pela primeira vez

-- Configurações de performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Configurações de conexão
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- Recarregar configurações
SELECT pg_reload_conf();

-- Criar extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Criar índices otimizados (serão criados pelas migrações do Alembic)
-- Aqui apenas definimos configurações iniciais

-- Configurar timezone
SET timezone = 'UTC';

-- Log de inicialização
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL inicializado com sucesso para YouTube Download API';
    RAISE NOTICE 'Database: youtube_downloads';
    RAISE NOTICE 'User: youtube_user';
    RAISE NOTICE 'Timezone: UTC';
END $$; 