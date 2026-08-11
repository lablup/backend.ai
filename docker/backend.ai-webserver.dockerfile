# Build context MUST be the repository root.  Starts FROM the shared
# backend.ai-base image (docker/backend.ai-base.dockerfile), which must be
# buildable at the same PKGVER — bake builds both (see docker-bake.hcl):
#   docker buildx bake backend_ai-webserver --set '*.platform=linux/amd64' --load
ARG PKGVER
FROM lablup/backend.ai-base:${PKGVER}

# Create necessary directories
RUN mkdir -p /var/log/backend.ai /etc/backend.ai

# Set working directory
WORKDIR /app

CMD ["backend.ai", "web", "start-server", "-f", "/etc/backend.ai/webserver.conf"]
