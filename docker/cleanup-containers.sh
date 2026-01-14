#!/bin/bash
# Script para limpar containers e volumes órfãos

set -e

echo "=== Limpando containers e volumes órfãos ==="

# Parar todos os containers relacionados
echo "Parando containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# Remover containers parados
echo "Removendo containers parados..."
docker ps -a --filter "name=docker-" --format "{{.ID}}" | xargs -r docker rm -f 2>/dev/null || true

# Limpar volumes órfãos (cuidado: isso remove volumes não usados)
echo "Verificando volumes órfãos..."
docker volume ls --filter "dangling=true" -q | xargs -r docker volume rm 2>/dev/null || true

# Limpar redes órfãs
echo "Limpando redes órfãs..."
docker network prune -f

# Verificar volumes do projeto
echo ""
echo "Volumes do projeto:"
docker volume ls | grep -E "(pgdata|redisdata|celerybeat|staticfiles|media|frontend_dist|letsencrypt|certbot)" || echo "Nenhum volume encontrado"

echo ""
echo "=== Limpeza concluída ==="
echo ""
echo "Para recriar os containers:"
echo "  cd /opt/nft_portal"
echo "  export REGISTRY=ghcr.io IMAGE_NAME=fmartns/nftmarketplace.com.br TAG=latest"
echo "  docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d"
