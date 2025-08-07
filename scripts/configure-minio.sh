#!/bin/bash

# MinIO Configuration Script for Backend.AI Development Environment
# This script configures MinIO storage for the Backend.AI halfstack setup

set -e

# Source utility functions if available
if [ -f "$(dirname "$0")/utils.sh" ]; then
    source "$(dirname "$0")/utils.sh"
else
    # Define basic utility functions if utils.sh is not available
    show_info() { echo "INFO: $1"; }
    show_warning() { echo "WARNING: $1"; }
    show_error() { echo "ERROR: $1"; }
fi

# Check if required variables are set
if [ -z "$docker_sudo" ]; then
    docker_sudo=""
fi

configure_minio() {
    local compose_file="${1:-docker-compose.halfstack.current.yml}"

    show_info "Configuring MinIO storage..."

    # Find MinIO container
    MINIO_CONTAINER_ID=$($docker_sudo docker compose -f "$compose_file" ps | grep "[-_]backendai-half-minio[-_]" | awk '{print $1}')

    if [ -z "$MINIO_CONTAINER_ID" ]; then
        show_warning "MinIO container not found, using default credentials"
        export MINIO_ACCESS_KEY="minioadmin"
        export MINIO_SECRET_KEY="minioadmin"
        return 1
    fi

    # Wait for MinIO container to be healthy
    show_info "Waiting for MinIO to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if $docker_sudo docker exec $MINIO_CONTAINER_ID curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
            break
        fi
        attempt=$((attempt + 1))
        echo "Waiting for MinIO... ($attempt/$max_attempts)"
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        show_warning "MinIO did not become ready in time, using default credentials"
        export MINIO_ACCESS_KEY="minioadmin"
        export MINIO_SECRET_KEY="minioadmin"
        return 1
    fi

    # Create MinIO configuration and credentials
    show_info "Setting up MinIO user and bucket..."
    $docker_sudo docker exec $MINIO_CONTAINER_ID sh -c "
        # Create mc alias for the MinIO instance
        mc alias set localminio http://localhost:9000 minioadmin minioadmin

        # Create a new user for Backend.AI
        MINIO_ACCESS_KEY=\$(cat /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 20)
        MINIO_SECRET_KEY=\$(cat /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 40)
        mc admin user add localminio \$MINIO_ACCESS_KEY \$MINIO_SECRET_KEY
        mc admin policy attach localminio readwrite --user \$MINIO_ACCESS_KEY

        # Create a bucket for Backend.AI
        mc mb localminio/backendai-storage

        # Output the credentials
        echo \"MINIO_ACCESS_KEY=\$MINIO_ACCESS_KEY\"
        echo \"MINIO_SECRET_KEY=\$MINIO_SECRET_KEY\"
    " > minio_credentials.tmp

    # Extract credentials from the output
    MINIO_ACCESS_KEY=$(grep "MINIO_ACCESS_KEY=" minio_credentials.tmp | cut -d'=' -f2)
    MINIO_SECRET_KEY=$(grep "MINIO_SECRET_KEY=" minio_credentials.tmp | cut -d'=' -f2)
    rm -f minio_credentials.tmp

    if [ -n "$MINIO_ACCESS_KEY" ] && [ -n "$MINIO_SECRET_KEY" ]; then
        show_info "MinIO credentials generated successfully"
        show_info "Access Key: $MINIO_ACCESS_KEY"
        export MINIO_ACCESS_KEY
        export MINIO_SECRET_KEY
        return 0
    else
        show_warning "Failed to generate MinIO credentials, using default credentials"
        export MINIO_ACCESS_KEY="minioadmin"
        export MINIO_SECRET_KEY="minioadmin"
        return 1
    fi
}

# Main function when script is called directly
main() {
    configure_minio
}

# Only run main if script is executed directly (not sourced)
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
