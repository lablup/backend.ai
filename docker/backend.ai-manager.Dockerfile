ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
COPY requirements.txt /requirements.txt
# Install dependencies from requirements.txt to respect version constraints
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt
# Install backend.ai packages from /dist (these are not in requirements.txt or PyPI)
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-manager==${PKGVER} --find-links=/dist --no-deps

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
COPY dist /dist
# Install all wheels and also look in /dist for backend.ai packages
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl

# Create necessary directories
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai /app/fixtures

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY docker/backend.ai-manager-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the default command to run the entrypoint script
CMD ["/app/entrypoint.sh"]
