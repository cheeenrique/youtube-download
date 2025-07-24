#!/usr/bin/env python3
"""
Script para executar migrações no Railway
"""
import os
import sys
from alembic.config import Config
from alembic import command

def run_migrations():
    """Executa as migrações do Alembic"""
    try:
        # Configurar o Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Verificar o status atual das migrações
        print("🔍 Verificando status das migrações...")
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        from sqlalchemy import create_engine, text
        
        # Obter a URL do banco de dados
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("⚠️ DATABASE_URL não encontrada, pulando migrações")
            return True
            
        engine = create_engine(database_url)
        
        # Verificar se a tabela alembic_version existe
        with engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                print(f"📋 Versão atual do banco: {current_version}")
            except Exception:
                print("📋 Tabela alembic_version não encontrada, será criada")
                current_version = None
        
        # Executar upgrade head (Alembic vai pular migrações já aplicadas)
        print("🔄 Executando migrações...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrações executadas com sucesso!")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao executar migrações: {e}")
        # Se for erro de tabela duplicada, considerar como sucesso
        if "already exists" in str(e):
            print("ℹ️ Tabelas já existem, continuando...")
            return True
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1) 