FROM redis:5-alpine

COPY configs/redis/sentinel.conf /etc/redis-sentinel.conf

CMD sed -i'' "s/REDIS_PASSWORD/${REDIS_PASSWORD}/g" /etc/redis-sentinel.conf; \
    redis-server /etc/redis-sentinel.conf --sentinel


# vim: ft=dockerfile
