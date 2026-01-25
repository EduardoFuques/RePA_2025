# Etapa de construcción
FROM node:20-alpine as build

# Directorio de trabajo
WORKDIR /app

# La API se accede via proxy reverso en /api
ENV VITE_API_URL=""

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar el resto de los archivos
COPY . .

# Construir la aplicación
RUN npm run build

# Etapa de producción
FROM nginx:stable-alpine

# Copiar la configuración personalizada de nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Configurar nginx como proxy reverso
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
