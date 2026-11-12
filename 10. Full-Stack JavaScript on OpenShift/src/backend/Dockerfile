FROM node:22-alpine
WORKDIR /opt/app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund
COPY server.mjs ./
ENV NODE_ENV=production PORT=8080
EXPOSE 8080
USER 10001
CMD ["node","server.mjs"]
