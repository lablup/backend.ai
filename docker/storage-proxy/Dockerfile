# syntax=docker/dockerfile:1.7

# -------- Stage 1: builder --------
# Build wheels for the storage-proxy and its internal dependencies using Pants.
# Run from the repo root:
#   git lfs install && git lfs pull
#   docker build -f docker/storage-proxy/Dockerfile -t backend.ai-storage-proxy:dev .
FROM python:3.13.7-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
        libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
ENV PATH=/root/.local/bin:${PATH}

WORKDIR /workspace
COPY . /workspace

RUN pants package \
        src/ai/backend/cli:dist \
        src/ai/backend/common:dist \
        src/ai/backend/logging:dist \
        src/ai/backend/plugin:dist \
        src/ai/backend/storage:dist

# -------- Stage 2: runtime --------
FROM python:3.13.7-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/backend.ai/venv \
    PATH=/opt/backend.ai/venv/bin:$PATH \
    BACKEND_CONFIG_PATH=/etc/backend.ai/storage-proxy.toml

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates libffi8 libssl3 tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 backendai \
    && useradd  --system --uid 1000 --gid backendai --home /home/backendai --shell /usr/sbin/nologin backendai \
    && mkdir -p /etc/backend.ai /var/lib/backend.ai /var/log/backend.ai /tmp/backend.ai/ipc \
    && chown -R backendai:backendai /etc/backend.ai /var/lib/backend.ai /var/log/backend.ai /tmp/backend.ai

RUN python -m venv "$VIRTUAL_ENV"

COPY --from=builder /workspace/dist/*.whl /tmp/wheels/
RUN pip install --upgrade pip \
 && pip install /tmp/wheels/*.whl \
 && rm -rf /tmp/wheels

# Run as root: storage-proxy needs to mkdir/chown on the NFS-backed hostPath
# (`/vfroot`) which is typically owned by root on the NFS server side. Using
# root avoids UID/GID mismatch headaches in lab setups. Swap to backendai
# UID in production where NFS is exported with proper uid mapping.
WORKDIR /root

ENTRYPOINT ["/usr/bin/tini", "--", "backend.ai"]
CMD ["storage", "start-server", "--config", "/etc/backend.ai/storage-proxy.toml"]
