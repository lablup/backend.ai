ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER
COPY ./dist /dist
COPY ./requirements.txt /requirements.txt
# Install dependencies from requirements.txt to respect version constraints
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt
# Install backend.ai packages from /dist (these are not in requirements.txt or PyPI)
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-agent==${PKGVER} --find-links=/dist --no-deps

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
COPY ./dist /dist
# Install all wheels and also look in /dist for backend.ai packages
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl

# Docker CLI for DooD: the agent shells out to `docker load` / `docker exec`
# against the host daemon socket. The binary is statically linked, so copying
# it from the official CLI image works on this glibc base without any apt
# repository setup. CLI <-> daemon API compatibility is wide; the tag is pinned
# for reproducibility, not to match the host daemon version.
COPY --from=docker:29.7.1-cli /usr/local/bin/docker /usr/local/bin/docker

# Create necessary directories
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai /var/lib/backend.ai

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY ./docker/backend.ai-agent-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "ai.backend.agent.server", "-f", "/etc/backend.ai/agent.toml"]
