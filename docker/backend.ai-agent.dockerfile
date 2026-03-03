ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY dist /dist
COPY requirements.txt /requirements.txt
# Install dependencies from requirements.txt to respect version constraints
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt
# Install backend.ai packages from /dist (these are not in requirements.txt or PyPI)
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-agent==${PKGVER} --find-links=/dist --no-deps

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
COPY dist /dist
# Install all wheels and also look in /dist for backend.ai packages
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl

# Install Docker CLI for DooD (Docker-out-of-Docker) operations
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai \
    /var/lib/backend.ai /app/scratches

# Set working directory
WORKDIR /app

CMD ["backend.ai", "ag", "start-server", "-f", "/etc/backend.ai/agent.toml"]
