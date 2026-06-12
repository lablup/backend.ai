FROM valkey/valkey:9.1.0-alpine

COPY configs/redis/sentinel.conf /etc/redis-sentinel.conf

CMD sed -i'' "s/REDIS_PASSWORD/${REDIS_PASSWORD}/g" /etc/redis-sentinel.conf; \
    valkey-sentinel /etc/redis-sentinel.conf


# vim: ft=dockerfile
