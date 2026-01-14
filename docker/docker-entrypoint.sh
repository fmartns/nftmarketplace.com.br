#!/bin/bash
set -e

# Sempre garantir que o ambiente virtual está configurado corretamente
# Isso é necessário porque o volume mount pode sobrescrever o .venv do container
echo "Verificando ambiente virtual..."

# Verificar se o .venv existe e está funcional
VENV_OK=false
if [ -d "/app/.venv" ] && [ -f "/app/.venv/bin/python" ]; then
    # Verificar se o Python do venv é compatível (Linux, não Mac)
    PYTHON_PLATFORM=$(/app/.venv/bin/python -c "import platform; print(platform.system())" 2>/dev/null || echo "UNKNOWN")
    
    # Se for Mac ou não conseguir detectar, o venv veio do host e precisa ser recriado
    if [ "$PYTHON_PLATFORM" = "Darwin" ] || [ "$PYTHON_PLATFORM" = "UNKNOWN" ]; then
        echo "Detectado .venv do host (Mac), será recriado..."
        VENV_OK=false
    else
        # Testar se Django e Pillow estão instalados e funcionando
        if /app/.venv/bin/python -c "import django; import PIL; from PIL import Image" 2>/dev/null; then
            VENV_OK=true
        fi
    fi
fi

# Se o venv não existe ou não está funcional, recriar
if [ ! -d "/app/.venv" ] || [ "$VENV_OK" = false ]; then
    if [ ! -d "/app/.venv" ]; then
        echo "Criando novo ambiente virtual..."
    else
        echo "Ambiente virtual corrompido, recriando..."
        # Remover ambiente quebrado
        rm -rf /app/.venv
        # Limpar cache do Poetry
        poetry cache clear pypi --all -n 2>/dev/null || true
    fi
    
    # Criar novo ambiente e instalar dependências
    poetry env use python3
    poetry install --only=main --no-root --no-cache
    
    # Verificar se a instalação foi bem-sucedida
    if ! /app/.venv/bin/python -c "import django; import PIL; from PIL import Image" 2>/dev/null; then
        echo "ERRO: Instalação falhou, tentando novamente sem cache..."
        poetry install --only=main --no-root --no-cache
    fi
else
    echo "Ambiente virtual está OK"
fi

# Executar o comando passado
exec "$@"
