#!/bin/bash
# Script para diagnosticar problemas do nginx

echo "=== Diagnóstico do Nginx ==="
echo ""

echo "1. Verificando logs do nginx:"
docker logs docker-nginx-1 --tail 50 2>&1 | head -30
echo ""

echo "2. Verificando se o serviço 'web' está acessível:"
docker exec docker-nginx-1 ping -c 2 web 2>&1 || echo "ERRO: Não consegue fazer ping no serviço 'web'"
echo ""

echo "3. Verificando volumes montados:"
docker inspect docker-nginx-1 --format='{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' 2>&1
echo ""

echo "4. Verificando se os diretórios existem nos volumes:"
docker exec docker-nginx-1 ls -la /usr/share/nginx/html/ 2>&1 | head -10 || echo "ERRO: Volume frontend_dist não montado corretamente"
echo ""

echo "5. Verificando configuração do nginx:"
docker exec docker-nginx-1 nginx -t 2>&1
echo ""

echo "6. Verificando status do serviço web:"
docker ps --filter "name=web" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== Fim do diagnóstico ==="
