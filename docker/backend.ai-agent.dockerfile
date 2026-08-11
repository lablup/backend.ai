# Build context MUST be the repository root (the paths below are context-relative):
#   docker build -f docker/backend.ai-agent.dockerfile --build-arg PYTHON_VERSION=<ver> --build-arg PKGVER=<ver> .
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
ENV PYTHONUNBUFFERED=1
COPY --from=builder /wheels /wheels
COPY ./dist /dist
# Install all wheels (looking in /dist for backend.ai packages) and drop the
# wheel/dist inputs in the same layer to keep the image slim
RUN pip install --no-cache-dir --find-links=/dist /wheels/*.whl && rm -rf /wheels /dist

# Docker CLI for DooD: the agent shells out to `docker load` / `docker exec`
# against the host daemon socket. The binary is statically linked, so copying
# it from the official CLI image works on this glibc base without any apt
# repository setup. CLI <-> daemon API compatibility is wide; the version is
# pinned (by digest, for reproducibility), not to match the host daemon.
# docker:29.7.1-cli
COPY --from=docker@sha256:27a51d5ab1cd38d9eeaba7b415b8c07bc10c31e1cf1ec8d78f6413fcfab3f44f /usr/local/bin/docker /usr/local/bin/docker

# Create necessary directories. NOTE: /var/lib/backend.ai/krunner itself is
# deliberately NOT created here — the entrypoint uses its absence (and the
# parent not being a mountpoint) to detect a missing host parity mount and
# fail fast.
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai /var/lib/backend.ai

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY --chmod=0755 ./docker/backend.ai-agent-entrypoint.sh /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "ai.backend.agent.server", "-f", "/etc/backend.ai/agent.toml"]
