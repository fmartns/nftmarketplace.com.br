#!/bin/bash
# Script para garantir que o PostgreSQL seja inicializado com as credenciais corretas do .env

set -e

echo "=== Verificando configuração do PostgreSQL ==="

# Carregar variáveis do .env
if [ ! -f "../.env" ]; then
    echo "ERRO: Arquivo .env não encontrado!"
    exit 1
fi

export $(cat ../.env | grep -v '^#' | xargs)

# Valores padrão se não estiverem no .env
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
POSTGRES_DB=${POSTGRES_DB:-nft_portal}
POSTGRES_DATA_DIR="../data/postgres"

echo "Configuração esperada:"
echo "  POSTGRES_USER: $POSTGRES_USER"
echo "  POSTGRES_DB: $POSTGRES_DB"
echo ""

# Verificar se o diretório de dados existe
if [ -d "$POSTGRES_DATA_DIR" ] && [ "$(ls -A $POSTGRES_DATA_DIR 2>/dev/null)" ]; then
    echo "⚠️  Diretório de dados do PostgreSQL já existe: $POSTGRES_DATA_DIR"
    echo ""
    echo "O PostgreSQL só cria o usuário na primeira inicialização."
    echo "Se o banco foi criado com outro usuário, você precisa:"
    echo ""
    echo "Opção 1: Recriar o banco (APAGA TODOS OS DADOS)"
    echo "  cd docker"
    echo "  docker compose down"
    echo "  rm -rf ../data/postgres"
    echo "  docker compose up -d db"
    echo ""
    echo "Opção 2: Criar o usuário manualmente no banco existente"
    echo "  cd docker"
    echo "  docker compose up -d db"
    echo "  docker compose exec db psql -U postgres -c \"CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';\""
    echo "  docker compose exec db psql -U postgres -c \"ALTER USER $POSTGRES_USER CREATEDB;\""
    echo "  docker compose exec db psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;\""
    echo ""
    read -p "Deseja recriar o banco agora? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo "Parando containers..."
        docker compose down 2>/dev/null || true
        echo "Removendo dados antigos..."
        rm -rf "$POSTGRES_DATA_DIR"
        echo "✅ Dados removidos. Execute 'docker compose up -d' para criar o banco com as credenciais corretas."
    else
        echo "Mantendo dados existentes. Certifique-se de que o usuário '$POSTGRES_USER' existe no banco."
    fi
else
    echo "✅ Diretório de dados não existe. O PostgreSQL será inicializado com as credenciais do .env na primeira execução."
    echo ""
    echo "Para iniciar:"
    echo "  cd docker"
    echo "  docker compose up -d db"
fi
