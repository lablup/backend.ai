# Backend.AI Agent for Kubernetes
# Requires pre-built wheels from pants package
# Using NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install Python 3.13 and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python runtime (using deadsnakes PPA for Python 3.13)
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    # Required for Kubernetes API client
    ca-certificates \
    # Required for networking
    iproute2 \
    # Utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Make python3.13 the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.13 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1

# Ensure pip is available for python3.13
RUN python3.13 -m ensurepip --upgrade && \
    python3.13 -m pip install --upgrade pip

# Copy pre-built wheels from host (built via pants package)
COPY dist/backend_ai_common-*.whl /wheels/
COPY dist/backend_ai_agent-*.whl /wheels/
COPY dist/backend_ai_kernel_binary-*-manylinux2014_aarch64*.whl /wheels/
COPY dist/backend_ai_cli-*.whl /wheels/
COPY dist/backend_ai_kernel_helper-*.whl /wheels/
COPY dist/backend_ai_kernel-*.whl /wheels/
COPY dist/backend_ai_logging-*.whl /wheels/
COPY dist/backend_ai_plugin-*.whl /wheels/
COPY dist/backend_ai_accelerator_cuda_open-*.whl /wheels/

# Install Backend.AI packages
# Note: Dependencies are already resolved in wheels from pants
RUN python3.13 -m pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels ~/.cache/pip

# Create non-root user for agent
RUN useradd -m -u 1000 -s /bin/bash backendai

# Create required directories
RUN mkdir -p \
    /var/lib/backend.ai \
    /tmp/backend.ai/ipc \
    /tmp/backend.ai/commit \
    && chown -R backendai:backendai /var/lib/backend.ai /tmp/backend.ai

# Set working directory
WORKDIR /home/backendai

# Switch to non-root user
USER backendai

# Expose ports
# Note: Actual ports are configured in agent.toml at runtime
# When running in K8s, pods use default ports (6001 RPC, 6003 HTTP)
# NodePort service maps external ports (30001, 30003) to pod ports
# We don't specify EXPOSE since it varies by deployment and is documentation-only anyway

# Health check
# Disabled - Use Kubernetes livenessProbe/readinessProbe instead
# Example K8s probe:
#   livenessProbe:
#     httpGet:
#       path: /health
#       port: 6003
HEALTHCHECK NONE

# Entrypoint
ENTRYPOINT ["python3.13", "-m", "ai.backend.agent.server"]
