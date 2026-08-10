# Build context MUST be the repository root (the paths below are context-relative):
#   docker build -f docker/backend.ai-storage-proxy.dockerfile --build-arg PYTHON_VERSION=<ver> --build-arg PKGVER=<ver> .
ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY ./dist /dist
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-storage-proxy==${PKGVER} --find-links=/dist

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels /dist

# Create necessary directories
RUN mkdir -p /var/log/backend.ai /etc/backend.ai

# Set working directory
WORKDIR /app

CMD ["python", "-m", "ai.backend.storage.server", "-f", "/etc/backend.ai/storage-proxy.toml"]
