# Build context MUST be the repository root.  Starts FROM the shared
# backend.ai-base image (docker/backend.ai-base.dockerfile), which must be
# buildable at the same PKGVER — bake builds both (see docker-bake.hcl):
#   docker buildx bake backend_ai-agent --set '*.platform=linux/amd64' --load
ARG PKGVER
FROM backend.ai-base:${PKGVER}

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
CMD ["backend.ai", "ag", "start-server", "-f", "/etc/backend.ai/agent.toml"]
