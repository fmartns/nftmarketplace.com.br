#!/bin/bash
# Script para corrigir a configuração do nginx baseado na existência dos certificados SSL
# Se os certificados não existirem, chama setup-ssl.sh para criá-los

set -e

NGINX_CONF_DIR="/opt/nft_portal/docker/nginx"
CERT_PATH="/var/lib/docker/volumes/docker_letsencrypt/_data/live/nftmarketplace.com.br/fullchain.pem"

echo "=== Verificando configuração do Nginx ==="

# Verificar se os certificados existem
if [ -f "$CERT_PATH" ]; then
    echo "✅ Certificados SSL encontrados em $CERT_PATH"
    echo "Usando configuração HTTPS (nginx.ssl.conf)"
    
    # Verificar se já está usando SSL
    if grep -q "ssl_certificate" "$NGINX_CONF_DIR/nginx.conf" 2>/dev/null; then
        echo "Nginx já está configurado para HTTPS"
    else
        echo "Alternando para configuração HTTPS..."
        cp "$NGINX_CONF_DIR/nginx.ssl.conf" "$NGINX_CONF_DIR/nginx.conf"
        echo "✅ Configuração HTTPS aplicada"
    fi
else
    echo "⚠️  Certificados SSL não encontrados"
    echo ""
    read -p "Deseja criar os certificados SSL agora? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        echo ""
        echo "Chamando setup-ssl.sh para criar certificados..."
        cd "$(dirname "$0")"
        ./setup-ssl.sh
        exit $?
    fi
    
    echo "Usando configuração HTTP (nginx.conf.orig)"
    
    # Verificar se já está usando HTTP
    if ! grep -q "ssl_certificate" "$NGINX_CONF_DIR/nginx.conf" 2>/dev/null; then
        echo "Nginx já está configurado para HTTP"
    else
        echo "Alternando para configuração HTTP..."
        if [ -f "$NGINX_CONF_DIR/nginx.conf.orig" ]; then
            cp "$NGINX_CONF_DIR/nginx.conf.orig" "$NGINX_CONF_DIR/nginx.conf"
        else
            echo "ERRO: nginx.conf.orig não encontrado!"
            echo "Restaurando configuração HTTP básica..."
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
        fi
        echo "✅ Configuração HTTP aplicada"
    fi
fi

echo ""
echo "=== Reiniciando nginx ==="
cd /opt/nft_portal
docker-compose -f docker/docker-compose.prod.yml --env-file .env restart nginx || true

echo ""
echo "=== Verificando status do nginx ==="
sleep 3
docker ps --filter "name=nginx" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=== Fim ==="
