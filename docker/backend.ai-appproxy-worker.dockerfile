ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-appproxy-worker==${PKGVER} --find-links=/dist

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl

# Create necessary directories
RUN mkdir -p /var/log/backend.ai /etc/backend.ai

# Set working directory
WORKDIR /app

CMD ["python", "-m", "ai.backend.appproxy.worker.server", "-f", "/etc/backend.ai/proxy-worker.toml"]

