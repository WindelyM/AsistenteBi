# Dockerfile para frontend-bi
FROM node:20-slim AS build

# Directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias
COPY package*.json ./

# Instala las dependencias
RUN npm install --legacy-peer-deps

# Copia el resto de los archivos
COPY . .

# Construye la aplicación
RUN npm run build

# Etapa final
FROM node:20-slim

# Directorio de trabajo
WORKDIR /app

# Instala serve globalmente
RUN npm install -g serve

# Copia la aplicación construida
COPY --from=build /app/dist ./dist

# Expone el puerto 3000
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
