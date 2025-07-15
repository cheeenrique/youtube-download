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
        
        # Executar upgrade head
        print("🔄 Executando migrações...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrações executadas com sucesso!")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao executar migrações: {e}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1) 