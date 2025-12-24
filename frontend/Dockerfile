FROM node:20-alpine as deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

FROM node:20-alpine as build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
# Call vite via node to avoid executable permission issues in some environments
RUN node ./node_modules/vite/bin/vite.js build

# Production stage: serve static files with nginx
FROM nginx:1.27-alpine as prod
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# Development stage: run Vite dev server
FROM node:20-alpine as dev
WORKDIR /app
COPY package.json package-lock.json ./
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Garantir permissões de execução para os binários do node_modules
RUN chmod +x node_modules/.bin/* || true
ENV VITE_API_BASE_URL="http://localhost:8001"
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
