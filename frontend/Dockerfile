FROM node:20-alpine AS dependencies
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS lint
COPY . .
RUN npm run lint

FROM lint AS build
ARG VITE_WS_BASE=ws://localhost:8000
ENV VITE_WS_BASE=${VITE_WS_BASE}
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
