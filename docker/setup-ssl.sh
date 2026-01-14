#!/bin/bash
# Script para configurar certificados SSL automaticamente

set -e

echo "=== Configuração de Certificados SSL ==="
echo ""

# Carregar variáveis do .env se existir
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Variáveis
DOMAIN="nftmarketplace.com.br"
DOMAINS="$DOMAIN www.$DOMAIN api.$DOMAIN"
EMAIL="${LE_EMAIL:-admin@$DOMAIN}"
CERT_PATH="/var/lib/docker/volumes/docker_letsencrypt/_data/live/$DOMAIN/fullchain.pem"
NGINX_CONF_DIR="/opt/nft_portal/docker/nginx"

echo "Domínios: $DOMAINS"
echo "Email: $EMAIL"
echo ""

# Verificar se os certificados já existem
if [ -f "$CERT_PATH" ]; then
    echo "✅ Certificados SSL já existem em $CERT_PATH"
    echo ""
    
    # Verificar se o nginx está usando HTTPS
    if grep -q "ssl_certificate" "$NGINX_CONF_DIR/nginx.conf" 2>/dev/null; then
        echo "✅ Nginx já está configurado para HTTPS"
        echo "Nada a fazer."
        exit 0
    else
        echo "⚠️  Certificados existem mas nginx está usando HTTP"
        echo "Alternando para configuração HTTPS..."
        cp "$NGINX_CONF_DIR/nginx.ssl.conf" "$NGINX_CONF_DIR/nginx.conf"
        cd /opt/nft_portal
        docker-compose -f docker/docker-compose.prod.yml --env-file .env restart nginx
        echo "✅ Nginx configurado para HTTPS"
        exit 0
    fi
fi

echo "⚠️  Certificados SSL não encontrados"
echo "Iniciando processo de obtenção de certificados..."
echo ""

# Verificar se o nginx está rodando
if ! docker ps --format '{{.Names}}' | grep -q '^docker-nginx-1$'; then
    echo "⚠️  Nginx não está rodando. Iniciando nginx com configuração HTTP..."
    
    # Garantir que está usando configuração HTTP
    if [ -f "$NGINX_CONF_DIR/nginx.conf.orig" ]; then
        cp "$NGINX_CONF_DIR/nginx.conf.orig" "$NGINX_CONF_DIR/nginx.conf"
    fi
    
    cd /opt/nft_portal
    export REGISTRY=${REGISTRY:-ghcr.io}
    export IMAGE_NAME=${IMAGE_NAME:-fmartns/nftmarketplace.com.br}
    export TAG=${TAG:-latest}
    
    docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d nginx
    
    echo "Aguardando nginx iniciar..."
    sleep 10
fi

# Verificar se o certbot está rodando
if ! docker ps --format '{{.Names}}' | grep -q '^docker-certbot-1$'; then
    echo "⚠️  Certbot não está rodando. Iniciando certbot..."
    cd /opt/nft_portal
    export REGISTRY=${REGISTRY:-ghcr.io}
    export IMAGE_NAME=${IMAGE_NAME:-fmartns/nftmarketplace.com.br}
    export TAG=${TAG:-latest}
    
    docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d certbot
    sleep 5
fi

# Verificar se os domínios estão acessíveis
echo "Verificando se os domínios estão acessíveis..."
for domain in $DOMAINS; do
    if curl -s -o /dev/null -w "%{http_code}" "http://$domain/.well-known/acme-challenge/test" | grep -q "404\|403"; then
        echo "✅ $domain está acessível"
    else
        echo "⚠️  $domain pode não estar acessível (verifique DNS e firewall)"
    fi
done
echo ""

# Solicitar certificados
echo "Solicitando certificados SSL da Let's Encrypt..."
echo "Isso pode levar alguns minutos..."
echo ""

CERTBOT_CONTAINER=$(docker ps --format '{{.Names}}' | grep '^docker-certbot-1$' | head -1)

if [ -z "$CERTBOT_CONTAINER" ]; then
    echo "ERRO: Container certbot não encontrado!"
    exit 1
fi

# Executar certbot
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
    
    # Verificar se os certificados foram criados
    if [ -f "$CERT_PATH" ]; then
        echo "✅ Certificados confirmados em $CERT_PATH"
    else
        echo "⚠️  Certificados podem estar em outro local. Verificando volume..."
        docker exec "$CERTBOT_CONTAINER" ls -la /etc/letsencrypt/live/$DOMAIN/ || true
    fi
    
    # Alternar para configuração HTTPS
    echo ""
    echo "Alternando nginx para configuração HTTPS..."
    cp "$NGINX_CONF_DIR/nginx.ssl.conf" "$NGINX_CONF_DIR/nginx.conf"
    
    # Reiniciar nginx
    echo "Reiniciando nginx..."
    cd /opt/nft_portal
    docker-compose -f docker/docker-compose.prod.yml --env-file .env restart nginx
    
    echo ""
    echo "✅ Configuração SSL concluída!"
    echo ""
    echo "Aguardando nginx reiniciar..."
    sleep 5
    
    # Verificar status
    if docker ps --filter "name=nginx" --format "{{.Status}}" | grep -q "Up"; then
        echo "✅ Nginx está rodando com HTTPS"
    else
        echo "⚠️  Nginx pode ter problemas. Verifique os logs:"
        echo "   docker logs docker-nginx-1"
    fi
    
else
    echo ""
    echo "❌ ERRO: Falha ao obter certificados SSL"
    echo ""
    echo "Possíveis causas:"
    echo "  1. Domínios não estão apontando para este servidor"
    echo "  2. Porta 80 não está acessível publicamente"
    echo "  3. Firewall bloqueando conexões"
    echo "  4. Rate limit da Let's Encrypt (muitas tentativas recentes)"
    echo ""
    echo "Verifique os logs do certbot:"
    echo "   docker logs $CERTBOT_CONTAINER"
    echo ""
    echo "Mantendo configuração HTTP. Tente novamente mais tarde."
    exit 1
fi

echo ""
echo "=== Concluído ==="
