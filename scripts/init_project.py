#!/usr/bin/env python3
"""
Script para inicializar o projeto YouTube Download API
Cria diretórios necessários e configura o ambiente
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Criar diretórios necessários para o projeto"""
    directories = [
        "videos/permanent",
        "videos/temporary", 
        "videos/temp",
        "logs",
        "logs/nginx",
        "static",
        "media"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def create_env_file():
    """Criar arquivo .env se não existir"""
    if not os.path.exists(".env"):
        if os.path.exists("env.example"):
            with open("env.example", "r") as f:
                content = f.read()
            
            with open(".env", "w") as f:
                f.write(content)
            
            print("✅ Arquivo .env criado a partir do env.example")
        else:
            print("⚠️  Arquivo env.example não encontrado")
    else:
        print("✅ Arquivo .env já existe")

def check_dependencies():
    """Verificar dependências básicas"""
    print("\n🔍 Verificando dependências...")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 9:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print("❌ Python 3.9+ é necessário")
        return False
    
    # Verificar FFmpeg
    try:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg encontrado")
        else:
            print("⚠️  FFmpeg não encontrado - será necessário para downloads")
    except FileNotFoundError:
        print("⚠️  FFmpeg não encontrado - será necessário para downloads")
    
    return True

def main():
    """Função principal"""
    print("🚀 Inicializando YouTube Download API...\n")
    
    # Criar diretórios
    print("📁 Criando diretórios...")
    create_directories()
    
    # Criar arquivo .env
    print("\n⚙️  Configurando ambiente...")
    create_env_file()
    
    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Falha na verificação de dependências")
        sys.exit(1)
    
    print("\n🎉 Inicialização concluída!")
    print("\n📋 Próximos passos:")
    print("1. Configure as variáveis no arquivo .env")
    print("2. Execute: docker-compose up -d")
    print("3. Acesse: http://localhost/api/docs")
    print("\n📚 Documentação:")
    print("- README.md: Visão geral do projeto")
    print("- CHECKLIST.md: Status de implementação")
    print("- PROJECT_SPECIFICATION.md: Especificação completa")

if __name__ == "__main__":
    main() 