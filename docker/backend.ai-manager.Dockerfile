# Build context MUST be the repository root.  Starts FROM the shared
# backend.ai-base image (docker/backend.ai-base.dockerfile), which must be
# buildable at the same PKGVER — bake builds both (see docker-bake.hcl):
#   docker buildx bake backend_ai-manager --set '*.platform=linux/amd64' --load
ARG PKGVER
FROM lablup/backend.ai-base:${PKGVER}

# Create necessary directories
RUN mkdir -p /tmp/backend.ai/ipc /var/log/backend.ai /etc/backend.ai /app/fixtures

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY ./docker/backend.ai-manager-entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the default command to run the entrypoint script
CMD ["/app/entrypoint.sh"]
