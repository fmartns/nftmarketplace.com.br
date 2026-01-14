#!/bin/bash
# Wrapper script para docker-compose que carrega variáveis necessárias

set -e

# Carregar variáveis do .env se existir
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Valores padrão se não estiverem definidos
export REGISTRY=${REGISTRY:-ghcr.io}
export IMAGE_NAME=${IMAGE_NAME:-${GITHUB_REPOSITORY:-fmartns/nftmarketplace.com.br}}
export TAG=${TAG:-latest}

# Verificar se as variáveis necessárias estão definidas
if [ -z "$REGISTRY" ] || [ -z "$IMAGE_NAME" ] || [ -z "$TAG" ]; then
    echo "ERRO: Variáveis REGISTRY, IMAGE_NAME ou TAG não estão definidas!"
    echo ""
    echo "Defina essas variáveis no arquivo .env ou no ambiente:"
    echo "  REGISTRY=ghcr.io"
    echo "  IMAGE_NAME=fmartns/nftmarketplace.com.br"
    echo "  TAG=latest"
    exit 1
fi

echo "Usando configuração:"
echo "  REGISTRY: $REGISTRY"
echo "  IMAGE_NAME: $IMAGE_NAME"
echo "  TAG: $TAG"
echo ""

# Verificar se o arquivo .env existe
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "AVISO: Arquivo .env não encontrado em $ENV_FILE"
    echo "Usando valores padrão para variáveis não definidas."
    ENV_FILE=""
fi

# Executar docker-compose com as variáveis
if [ -n "$ENV_FILE" ]; then
    exec docker-compose -f docker-compose.prod.yml --env-file "$ENV_FILE" "$@"
else
    exec docker-compose -f docker-compose.prod.yml "$@"
fi
