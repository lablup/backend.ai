# Kernel runner image for Kubernetes sessions. An init container runs install.sh to copy
# the runner into an emptyDir that the session container mounts at /opt/backend.ai and /opt/kernel.
FROM alpine:3.20 AS extract
RUN apk add --no-cache xz
COPY context/ /context/
RUN set -eu; \
    for libc in static-gnu musllinux; do \
      mkdir -p /krunner/env/$libc; \
      tar xJf /context/krunner-env.$libc.tar.xz -C /krunner/env/$libc; \
      cp /context/krunner-python.$libc.txt /krunner/env/$libc/PYTHON_VERSION; \
      pyver=$(cat /context/krunner-python.$libc.txt); \
      site=/krunner/env/$libc/lib/python$pyver/site-packages/ai/backend; \
      rm -rf $site/kernel $site/helpers; \
      cp -a /context/kernel /context/helpers $site/; \
    done; \
    cp -a /context/runner /krunner/runner; \
    find /krunner -name __pycache__ -prune -exec rm -rf {} +

FROM busybox:1.36-musl
COPY --from=extract /krunner /krunner
COPY install.sh /krunner/install.sh
ENTRYPOINT ["/krunner/install.sh"]
