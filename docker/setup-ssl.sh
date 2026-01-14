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

# IMPORTANTE: Sempre garantir que está usando configuração HTTP antes de iniciar nginx
echo "Garantindo que nginx está usando configuração HTTP (necessário para obter certificados)..."
if [ -f "$NGINX_CONF_DIR/nginx.conf.orig" ]; then
    cp "$NGINX_CONF_DIR/nginx.conf.orig" "$NGINX_CONF_DIR/nginx.conf"
    echo "✅ Configuração HTTP restaurada de nginx.conf.orig"
elif [ -f "$NGINX_CONF_DIR/nginx.conf" ] && grep -q "ssl_certificate" "$NGINX_CONF_DIR/nginx.conf"; then
    echo "⚠️  nginx.conf.orig não encontrado, mas nginx.conf tem SSL. Criando configuração HTTP básica..."
    # Criar configuração HTTP básica
    cat > "$NGINX_CONF_DIR/nginx.conf" << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name nftmarketplace.com.br www.nftmarketplace.com.br;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/certbot/.well-known/acme-challenge/;
        default_type "text/plain";
        try_files $uri =404;
    }

    location ~ /\. { deny all; }
    location = /.env { return 404; }

    root /usr/share/nginx/html;
    index index.html;

    location ~* \.(?:js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot)$ {
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
        try_files $uri =404;
    }

    location / {
        try_files $uri /index.html;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name api.nftmarketplace.com.br;

    location ^~ /.well-known/acme-challenge/ {
        alias /var/www/certbot/.well-known/acme-challenge/;
        default_type "text/plain";
        try_files $uri =404;
    }

    location ~ /\. { deny all; }
    location = /.env { return 404; }

    location /static/ {
        alias /app/staticfiles/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
        try_files $uri =404;
    }
    location /media/ {
        alias /app/media/;
        access_log off;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        try_files $uri =404;
    }

    location / {
        proxy_pass http://web:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 25m;
        proxy_read_timeout 60s;
    }
}
EOF
    echo "✅ Configuração HTTP básica criada"
else
    echo "✅ Configuração HTTP já está correta"
fi

# Se o nginx estiver rodando, verificar se está usando HTTP e reiniciar se necessário
if docker ps --format '{{.Names}}' | grep -q '^docker-nginx-1$'; then
    echo ""
    echo "Nginx está rodando. Verificando configuração..."
    if grep -q "ssl_certificate" "$NGINX_CONF_DIR/nginx.conf"; then
        echo "⚠️  Nginx está usando configuração SSL mas certificados não existem!"
        echo "Parando nginx para atualizar configuração..."
        cd /opt/nft_portal
        docker-compose -f docker/docker-compose.prod.yml --env-file .env stop nginx 2>/dev/null || true
        sleep 2
    fi
fi

# Verificar se o nginx está rodando
if ! docker ps --format '{{.Names}}' | grep -q '^docker-nginx-1$'; then
    echo ""
    echo "⚠️  Nginx não está rodando. Verificando dependências..."
    
    # Verificar se o web está healthy
    WEB_HEALTHY=false
    if docker ps --format '{{.Names}}\t{{.Status}}' | grep '^docker-web-1' | grep -q 'healthy'; then
        WEB_HEALTHY=true
        echo "✅ Serviço web está healthy"
    else
        echo "⚠️  Serviço web não está healthy. Nginx precisa estar rodando para o desafio ACME."
        echo "Tentando iniciar nginx mesmo assim (pode falhar se web não estiver pronto)..."
    fi
    
    cd /opt/nft_portal
    export REGISTRY=${REGISTRY:-ghcr.io}
    export IMAGE_NAME=${IMAGE_NAME:-fmartns/nftmarketplace.com.br}
    export TAG=${TAG:-latest}
    
    # Tentar iniciar nginx normalmente primeiro
    if docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d nginx 2>&1 | grep -q "dependency\|unhealthy"; then
        echo ""
        echo "⚠️  Nginx não pode iniciar devido à dependência do web."
        echo "Aguardando web ficar healthy (timeout de 2 minutos)..."
        
        # Aguardar web ficar healthy
        TIMEOUT=120
        ELAPSED=0
        while [ $ELAPSED -lt $TIMEOUT ]; do
            if docker ps --format '{{.Names}}\t{{.Status}}' | grep '^docker-web-1' | grep -q 'healthy'; then
                echo "✅ Web está healthy agora. Tentando iniciar nginx novamente..."
                docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d nginx
                break
            fi
            sleep 5
            ELAPSED=$((ELAPSED + 5))
            echo "   Aguardando... (${ELAPSED}s/${TIMEOUT}s)"
        done
        
        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo ""
            echo "❌ Timeout: Web não ficou healthy a tempo."
            echo ""
            echo "Últimos logs do web:"
            docker logs docker-web-1 --tail 20 2>&1 || echo "Container web não encontrado"
            echo ""
            echo "Para diagnosticar o problema do web:"
            echo "  1. Verifique os logs: docker logs docker-web-1"
            echo "  2. Verifique o status: docker ps --filter name=web"
            echo "  3. Verifique dependências: docker ps --filter name=db --filter name=redis"
            echo ""
            echo "Depois que o web estiver funcionando, você pode:"
            echo "  - Executar este script novamente: ./setup-ssl.sh"
            echo "  - Ou iniciar o nginx manualmente: docker-compose -f docker/docker-compose.prod.yml --env-file .env up -d nginx"
            exit 1
        fi
    fi
    
    echo "Aguardando nginx iniciar..."
    sleep 10
    
    # Verificar se nginx iniciou
    if ! docker ps --format '{{.Names}}' | grep -q '^docker-nginx-1$'; then
        echo "❌ Nginx não iniciou. Verifique os logs: docker logs docker-nginx-1"
        exit 1
    fi
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
