# syntax=docker/dockerfile:1.7

# -------- Stage 1: builder --------
# Build wheels for the manager and its internal dependencies using Pants.
# Run from the repo root:
#   git lfs install && git lfs pull   # required: see docker/agent/Dockerfile
#   docker build -f docker/manager/Dockerfile -t backend.ai-manager:dev .
FROM python:3.13.7-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git curl ca-certificates \
        libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the Pants launcher (scie-pants). The pinned version in pants.toml is
# self-bootstrapped on first invocation (inside the workspace, below).
RUN curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh | bash
ENV PATH=/root/.local/bin:${PATH}

WORKDIR /workspace
COPY . /workspace

# Produce wheels for manager + its intra-repo dependencies.
# The generated wheels land in /workspace/dist/.
RUN pants package \
        src/ai/backend/cli:dist \
        src/ai/backend/common:dist \
        src/ai/backend/logging:dist \
        src/ai/backend/plugin:dist \
        src/ai/backend/manager:dist

# -------- Stage 2: runtime --------
FROM python:3.13.7-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/backend.ai/venv \
    PATH=/opt/backend.ai/venv/bin:$PATH \
    BACKEND_CONFIG_PATH=/etc/backend.ai/manager.toml

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates libffi8 libssl3 tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1000 backendai \
    && useradd  --system --uid 1000 --gid backendai --home /home/backendai --shell /usr/sbin/nologin backendai \
    && mkdir -p /etc/backend.ai /var/lib/backend.ai /var/log/backend.ai \
    && chown -R backendai:backendai /etc/backend.ai /var/lib/backend.ai /var/log/backend.ai

RUN python -m venv "$VIRTUAL_ENV"

# Install the manager wheels. Extra plugin wheels can be layered on top in a
# derived image: `FROM backend.ai-manager:x.y` + `RUN pip install backendai-plugin-*`.
COPY --from=builder /workspace/dist/*.whl /tmp/wheels/
RUN pip install --upgrade pip \
 && pip install /tmp/wheels/*.whl \
 && rm -rf /tmp/wheels

USER backendai
WORKDIR /home/backendai

# `backend.ai` is the unified CLI; the manager registers the `mgr` subcommand
# via the `backendai_cli_v10` entry point defined in src/ai/backend/manager/BUILD.
ENTRYPOINT ["/usr/bin/tini", "--", "backend.ai"]
CMD ["mgr", "start-server", "--config", "/etc/backend.ai/manager.toml"]
