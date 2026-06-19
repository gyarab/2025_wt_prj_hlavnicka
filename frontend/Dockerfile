# Frontend image: postaví Vue SPA (Vite) a servíruje ji nginxem.
#
# Tenhle nginx je zároveň VSTUPNÍ BRÁNA celé aplikace (publikuje port 80):
#   /app/    -> tahle Vue SPA (z buildu níže)
#   /static/ -> statické soubory Djanga (sdílený volume, plní je collectstatic)
#   /media/  -> média (sdílený volume)
#   /…       -> proxy na gunicorn (Django: rozcestník, /movies, /admin, /api, /accounts)
# Reálnou konfiguraci nginxu mountuje compose z deploy/config/nginx.conf.

# 1) build Vue do statických souborů
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Vue poběží pod /app/ (vedle Django frontendu), proto se mění base.
ENV VITE_BASE=/app/
RUN npm run build

# 2) runtime: nginx s nabuildovanou SPA
FROM nginx:1.27-alpine
# Hotová SPA; nginx.conf ji čeká v /usr/share/nginx/vue.
COPY --from=build /app/dist /usr/share/nginx/vue
EXPOSE 80
