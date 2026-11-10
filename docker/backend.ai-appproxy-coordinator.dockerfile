# Build context MUST be the repository root.  Starts FROM the shared
# backend.ai-base image (docker/backend.ai-base.dockerfile), which must be
# buildable at the same PKGVER — bake builds both (see docker-bake.hcl):
#   docker buildx bake backend_ai-appproxy-coordinator --set '*.platform=linux/amd64' --load
ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY ./dist /dist
COPY ./requirements.txt /requirements.txt
# Install dependencies from requirements.txt to respect version constraints
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt
# Install backend.ai packages from /dist (these are not in requirements.txt or PyPI)
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-appproxy-coordinator==${PKGVER} --find-links=/dist --no-deps

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
COPY ./dist /dist
# Install all wheels and also look in /dist for backend.ai packages
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl

# Create necessary directories
RUN mkdir -p /var/log/backend.ai /etc/backend.ai

# Set working directory
WORKDIR /app

CMD ["backend.ai", "app-proxy-coordinator", "start-server", "-f", "/etc/backend.ai/proxy-coordinator.toml"]
