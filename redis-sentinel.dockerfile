FROM redis:5-alpine

COPY configs/redis/sentinel.conf /etc/redis-sentinel.conf

CMD sed -i'' /etc/redis-sentinel.conf "s/REDIS_PASSWORD/${REDIS_PASSWORD}/g"; \
    redis-server /etc/redis-sentinel.conf --sentinel


# vim: ft=dockerfile
