FROM node:22-alpine
WORKDIR /opt/app
COPY package.json server.mjs ./
COPY public ./public
ENV NODE_ENV=production PORT=8080
EXPOSE 8080
USER 10001
CMD ["node","server.mjs"]
