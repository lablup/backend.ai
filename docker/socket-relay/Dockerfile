FROM alpine:3.12

RUN apk add --no-cache socat  # 1.7.3.4-r1

ENTRYPOINT ["/usr/bin/socat"]

LABEL ai.backend.system=1 \
      ai.backend.version=1
