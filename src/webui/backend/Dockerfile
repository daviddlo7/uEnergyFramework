FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install express

USER root
RUN apk add --no-cache curl tar
RUN curl -L https://github.com/fullstorydev/grpcurl/releases/download/v1.9.3/grpcurl_1.9.3_linux_x86_64.tar.gz | tar xz -C /usr/local/bin

COPY src/webui/backend/server.js .

EXPOSE 3000
CMD ["node", "server.js"]
