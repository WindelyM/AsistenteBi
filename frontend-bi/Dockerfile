# Etapa 1: Construcción
FROM node:20-slim AS build

WORKDIR /app

# Copia dependencias
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copia código fuente
COPY . .

# Construye la aplicación
RUN npm run build

# Etapa 2: Servidor Web (Nginx)
FROM nginx:alpine

# Copia el build de React al directorio de Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Copia configuración personalizada de Nginx si fuera necesaria (opcional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer el puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
