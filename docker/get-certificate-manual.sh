#!/bin/bash
# Script simplificado para obter certificados SSL manualmente

set -e

echo "=== Obtenção Manual de Certificados SSL ==="
echo ""

# Carregar variáveis do .env
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

DOMAIN="nftmarketplace.com.br"
DOMAINS="$DOMAIN www.$DOMAIN api.$DOMAIN"
EMAIL="${LE_EMAIL:-admin@$DOMAIN}"

echo "Domínios: $DOMAINS"
echo "Email: $EMAIL"
echo ""

# Verificar se nginx está usando HTTP
echo "1. Verificando configuração do nginx..."
cd /opt/nft_portal/docker

if grep -q "ssl_certificate" nginx/nginx.conf; then
    echo "⚠️  Nginx está usando SSL. Restaurando configuração HTTP..."
    if [ -f "nginx/nginx.conf.orig" ]; then
        cp nginx/nginx.conf.orig nginx/nginx.conf
        echo "✅ Configuração HTTP restaurada"
    else
        echo "❌ nginx.conf.orig não encontrado!"
        exit 1
    fi
else
    echo "✅ Nginx está usando HTTP"
fi

# Verificar se nginx está rodando
echo ""
echo "2. Verificando se nginx está rodando..."
if ! docker ps --format '{{.Names}}' | grep -q '^docker-nginx-1$'; then
    echo "⚠️  Nginx não está rodando. Iniciando..."
    cd /opt/nft_portal
    export REGISTRY=${REGISTRY:-ghcr.io}
    export IMAGE_NAME=${IMAGE_NAME:-fmartns/nftmarketplace.com.br}
    export TAG=${TAG:-latest}
    docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d nginx
    echo "Aguardando nginx iniciar..."
    sleep 10
else
    echo "✅ Nginx está rodando"
    # Reiniciar para garantir que está usando HTTP
    echo "Reiniciando nginx para aplicar configuração HTTP..."
    cd /opt/nft_portal
    docker-compose -f docker/docker-compose.prod.yml --env-file .env restart nginx
    sleep 5
fi

# Verificar se certbot está rodando
echo ""
echo "3. Verificando se certbot está rodando..."
if ! docker ps --format '{{.Names}}' | grep -q '^docker-certbot-1$'; then
    echo "⚠️  Certbot não está rodando. Iniciando..."
    cd /opt/nft_portal
    export REGISTRY=${REGISTRY:-ghcr.io}
    export IMAGE_NAME=${IMAGE_NAME:-fmartns/nftmarketplace.com.br}
    export TAG=${TAG:-latest}
    docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d certbot
    sleep 5
else
    echo "✅ Certbot está rodando"
fi

# Verificar DNS
echo ""
echo "4. Verificando DNS (os domínios devem apontar para este servidor)..."
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
echo "IP do servidor: $SERVER_IP"

for domain in $DOMAINS; do
    DOMAIN_IP=$(dig +short $domain | tail -1)
    if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
        echo "✅ $domain → $DOMAIN_IP (correto)"
    else
        echo "⚠️  $domain → $DOMAIN_IP (deveria ser $SERVER_IP)"
    fi
done

echo ""
read -p "Continuar mesmo se DNS não estiver correto? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Abortando. Configure o DNS primeiro."
    exit 1
fi

# Obter certificados
echo ""
echo "5. Obtendo certificados SSL da Let's Encrypt..."
echo "Isso pode levar alguns minutos..."
echo ""

CERTBOT_CONTAINER=$(docker ps --format '{{.Names}}' | grep '^docker-certbot-1$' | head -1)

if [ -z "$CERTBOT_CONTAINER" ]; then
    echo "❌ Container certbot não encontrado!"
    exit 1
fi

if docker exec "$CERTBOT_CONTAINER" certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    -d $DOMAINS; then
    
    echo ""
    echo "✅ Certificados SSL obtidos com sucesso!"
    echo ""
    
    # Verificar certificados
    echo "6. Verificando certificados criados..."
    docker exec "$CERTBOT_CONTAINER" ls -la /etc/letsencrypt/live/$DOMAIN/ || echo "⚠️  Certificados podem estar em outro local"
    
    # Atualizar nginx para HTTPS
    echo ""
    echo "7. Atualizando nginx para HTTPS..."
    cd /opt/nft_portal/docker
    cp nginx/nginx.ssl.conf nginx/nginx.conf
    echo "✅ Configuração HTTPS aplicada"
    
    # Reiniciar nginx
    echo ""
    echo "8. Reiniciando nginx..."
    cd /opt/nft_portal
    docker-compose -f docker/docker-compose.prod.yml --env-file .env restart nginx
    sleep 5
    
    # Verificar status
    echo ""
    echo "9. Verificando status final..."
    if docker ps --filter name=nginx --format "{{.Status}}" | grep -q "Up"; then
        echo "✅ Nginx está rodando com HTTPS"
        echo ""
        echo "Teste os domínios:"
        echo "  curl -I https://$DOMAIN"
        echo "  curl -I https://api.$DOMAIN"
    else
        echo "⚠️  Nginx pode ter problemas. Verifique os logs:"
        echo "  docker logs docker-nginx-1"
    fi
    
else
    echo ""
    echo "❌ ERRO: Falha ao obter certificados SSL"
    echo ""
    echo "Verifique os logs:"
    echo "  docker logs $CERTBOT_CONTAINER"
    echo ""
    echo "Possíveis causas:"
    echo "  - DNS não está apontando para o servidor"
    echo "  - Porta 80 não está acessível"
    echo "  - Rate limit da Let's Encrypt (muitas tentativas)"
    exit 1
fi

echo ""
echo "=== Concluído ==="
