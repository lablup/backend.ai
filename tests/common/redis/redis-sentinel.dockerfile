FROM redis:6-alpine

COPY ./sentinel.conf /etc/redis-sentinel.conf

CMD sed -i'' "s/REDIS_PASSWORD/${REDIS_PASSWORD}/g" /etc/redis-sentinel.conf; \
    sed -i'' "s/REDIS_MASTER_PORT/${REDIS_MASTER_PORT}/g" /etc/redis-sentinel.conf; \
    redis-server /etc/redis-sentinel.conf --sentinel --port ${REDIS_PORT}


# vim: ft=dockerfile
