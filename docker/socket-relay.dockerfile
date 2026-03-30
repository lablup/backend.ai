FROM alpine:3.17

RUN apk add --no-cache socat  # 1.7.4.4-r0

ENTRYPOINT ["/usr/bin/socat"]

LABEL ai.backend.system=1 \
      ai.backend.version=1
