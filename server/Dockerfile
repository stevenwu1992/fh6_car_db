# FH6 车辆索引 · 账号与数据服务（零依赖，仅 Node 22+）
FROM node:22-alpine
WORKDIR /app
COPY server ./server
COPY output ./output
ENV PORT=8787 \
    DB_PATH=/data/fh6.db \
    STATIC_DIR=/app/output \
    NODE_ENV=production
RUN mkdir -p /data && addgroup -S app && adduser -S app -G app && chown -R app /data
USER app
VOLUME ["/data"]
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8787/health || exit 1
CMD ["node", "server/server.mjs"]
