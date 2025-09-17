ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-manager==${PKGVER} --find-links=/dist

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN mkdir -p /root/.ssh
RUN apt-get update && apt-get install -y vim && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir /wheels/*.whl

# Create necessary directories
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai /app/fixtures

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the manager service port
EXPOSE 8091

# Set the default command to run the entrypoint script
CMD ["/app/entrypoint.sh"]
