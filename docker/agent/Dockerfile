# syntax=docker/dockerfile:1.7

# -------- Stage 1: builder --------
# Build wheels for the agent and its intra-repo dependencies using Pants.
# Run from the repo root:
#   git lfs install && git lfs pull   # required: krunner/nsenter binaries
#   docker build -f docker/agent/Dockerfile -t backend.ai-agent:dev .
# LFS note (todo.md §5.2 I-20): backendai-socket-relay.img.*.tar.gz and
# linuxkit-nsenter.img.*.tar.gz are LFS-tracked. Without `git lfs pull`, the
# wheels ship ~132-byte pointer files and the agent crashes at boot with
# `gzip.BadGzipFile: Not a gzipped file`.
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

# Produce wheels for agent + its intra-repo dependencies and the bundled
# accelerator plugins (cuda_open, mock). The generated wheels land in
# /workspace/dist/.
RUN pants package \
        src/ai/backend/cli:dist \
        src/ai/backend/common:dist \
        src/ai/backend/logging:dist \
        src/ai/backend/plugin:dist \
        src/ai/backend/kernel:dist \
        src/ai/backend/accelerator/cuda_open:dist \
        src/ai/backend/accelerator/mock:dist \
        src/ai/backend/agent:dist

# -------- Stage 2: runtime --------
FROM python:3.13.7-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/backend.ai/venv \
    PATH=/opt/backend.ai/venv/bin:$PATH \
    BACKEND_CONFIG_PATH=/etc/backend.ai/agent.toml

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates libffi8 libssl3 tini \
        iproute2 iputils-ping util-linux procps \
        curl \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli \
    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /etc/backend.ai /var/lib/backend.ai /var/run/backend.ai/ipc

RUN python -m venv "$VIRTUAL_ENV"

COPY --from=builder /workspace/dist/*.whl /tmp/wheels/
RUN pip install --upgrade pip \
 && pip install /tmp/wheels/*.whl \
 && rm -rf /tmp/wheels

# Run as root: the agent talks to /var/run/docker.sock and reads /proc, /sys,
# cgroups; in practice the DaemonSet will run privileged anyway. Keeping the
# default UID makes host-path perms a non-issue.
WORKDIR /root

ENTRYPOINT ["/usr/bin/tini", "--", "backend.ai"]
CMD ["ag", "start-server", "--config", "/etc/backend.ai/agent.toml"]
