#!/bin/bash
# Initialize etcd and Redis for standalone K8s agent testing
# This script:
# 1. Starts isolated etcd and Redis containers
# 2. Initializes etcd with minimal required configuration
#
# Based on scripts/install-dev.sh and docker-compose.halfstack-main.yml

set -e

RED="\033[0;91m"
GREEN="\033[0;92m"
YELLOW="\033[0;93m"
BLUE="\033[0;94m"
NC="\033[0m"

show_info() {
  echo -e "${BLUE}[INFO]${NC} ${GREEN}$1${NC}"
}

show_warn() {
  echo -e "${YELLOW}[WARN]${NC} ${YELLOW}$1${NC}"
}

show_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
ETCD_PORT="${ETCD_PORT:-2479}"
REDIS_PORT="${REDIS_PORT:-6479}"
ETCD_NAMESPACE="${ETCD_NAMESPACE:-test-standalone}"
ETCD_CONTAINER_NAME="backend-ai-test-etcd"
REDIS_CONTAINER_NAME="backend-ai-test-redis"

# Images from docker-compose.halfstack-main.yml
ETCD_IMAGE="${ETCD_IMAGE:-quay.io/coreos/etcd:v3.5.14}"
REDIS_IMAGE="${REDIS_IMAGE:-redis:7.2.11-alpine}"

show_info "Backend.AI Standalone K8s Test - Auto-Setup"
echo "  etcd port: $ETCD_PORT (image: $ETCD_IMAGE)"
echo "  Redis port: $REDIS_PORT (image: $REDIS_IMAGE)"
echo "  etcd namespace: $ETCD_NAMESPACE"
echo ""

# Detect if docker requires sudo
DOCKER_SUDO=""
if ! docker ps &>/dev/null; then
  if sudo docker ps &>/dev/null; then
    DOCKER_SUDO="sudo"
    show_warn "Docker requires sudo"
  else
    show_error "Docker is not available or permission denied"
    exit 1
  fi
fi

# Function to start etcd
start_etcd() {
  show_info "Starting etcd container..."

  # Check if container already exists
  if $DOCKER_SUDO docker ps -a --format '{{.Names}}' | grep -q "^${ETCD_CONTAINER_NAME}$"; then
    show_warn "Container $ETCD_CONTAINER_NAME already exists"

    # Check if it's running
    if $DOCKER_SUDO docker ps --format '{{.Names}}' | grep -q "^${ETCD_CONTAINER_NAME}$"; then
      show_info "etcd is already running"
      return 0
    else
      show_info "Starting existing container..."
      $DOCKER_SUDO docker start $ETCD_CONTAINER_NAME
      return 0
    fi
  fi

  # Create new container
  $DOCKER_SUDO docker run -d \
    --name $ETCD_CONTAINER_NAME \
    -p $ETCD_PORT:2379 \
    $ETCD_IMAGE \
    /usr/local/bin/etcd \
    --name backendai-test-etcd \
    --data-dir /etcd-data \
    --listen-client-urls http://0.0.0.0:2379 \
    --advertise-client-urls http://0.0.0.0:2379 \
    --listen-peer-urls http://0.0.0.0:2380 \
    --initial-advertise-peer-urls http://0.0.0.0:2380 \
    --initial-cluster backendai-test-etcd=http://0.0.0.0:2380 \
    --initial-cluster-token backendai-test-token \
    --initial-cluster-state new \
    --enable-v2=true \
    --auto-compaction-retention 1

  show_info "✓ etcd container started"
}

# Function to start Redis
start_redis() {
  show_info "Starting Redis container..."

  # Check if container already exists
  if $DOCKER_SUDO docker ps -a --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
    show_warn "Container $REDIS_CONTAINER_NAME already exists"

    # Check if it's running
    if $DOCKER_SUDO docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER_NAME}$"; then
      show_info "Redis is already running"
      return 0
    else
      show_info "Starting existing container..."
      $DOCKER_SUDO docker start $REDIS_CONTAINER_NAME
      return 0
    fi
  fi

  # Create new container
  # IMPORTANT: --bind 0.0.0.0 allows connections from K8s pods via host IP
  $DOCKER_SUDO docker run -d \
    --name $REDIS_CONTAINER_NAME \
    -p $REDIS_PORT:6379 \
    $REDIS_IMAGE \
    redis-server --bind 0.0.0.0 --appendonly yes

  show_info "✓ Redis container started"
}

# Start containers
start_etcd
start_redis

# Wait for services to be ready
show_info "Waiting for services to be ready..."
sleep 3

# Verify services are accessible
show_info "Verifying service connectivity..."

if ! nc -z localhost $ETCD_PORT 2>/dev/null; then
  show_error "etcd is not accessible on port $ETCD_PORT"
  echo "Check container logs: ${DOCKER_SUDO} docker logs $ETCD_CONTAINER_NAME"
  exit 1
fi

if ! nc -z localhost $REDIS_PORT 2>/dev/null; then
  show_error "Redis is not accessible on port $REDIS_PORT"
  echo "Check container logs: ${DOCKER_SUDO} docker logs $REDIS_CONTAINER_NAME"
  exit 1
fi

show_info "✓ Both services are accessible"

# Get host IP for agent connectivity (used for both NFS and Redis)
HOST_IP=$(hostname -I | awk '{print $1}')

# Use etcdctl for initialization
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=localhost:$ETCD_PORT

show_info "Initializing etcd with minimal configuration..."

# Backend.AI uses /sorna/ prefix for all etcd keys (legacy naming)
ETCD_PREFIX="/sorna/$ETCD_NAMESPACE"

# 1. Mock manager presence (so agent doesn't wait for manager detection)
etcdctl put "$ETCD_PREFIX/nodes/manager/test-manager" "up"
show_info "✓ Manager presence mocked"

# 2. Configure Redis (CRITICAL - agent reads this at startup)
# addr expects "host:port" string format, not JSON object
# IMPORTANT: Use host IP, not localhost, so K8s pod can access via host.k8s.internal
etcdctl put "$ETCD_PREFIX/config/redis/addr" "$HOST_IP:$REDIS_PORT"
show_info "✓ Redis configuration set (accessible from K8s at host.k8s.internal:$REDIS_PORT)"

# 3. Optional: Set redis-helper config (for image metadata management)
# This is used by ValkeyImageClient and expects timeout values
# NOTE: Must be stored as separate etcd keys, not a single JSON string
etcdctl put "$ETCD_PREFIX/config/redis/redis_helper_config/socket_timeout" "5.0"
etcdctl put "$ETCD_PREFIX/config/redis/redis_helper_config/socket_connect_timeout" "2.0"
etcdctl put "$ETCD_PREFIX/config/redis/redis_helper_config/reconnect_poll_timeout" "0.3"
show_info "✓ Redis helper config set"

# 4. Optional: Set container/agent configs (agent can override from local config)
# These are optional because agent-k8s-standalone.toml provides them locally
# But good to have for completeness

# No volumes config needed for minimal testing (not testing vfolder mounts)
# etcdctl put "/$ETCD_NAMESPACE/volumes" "{}"

show_info "✓ Etcd initialization complete!"

# Setup NFS server
echo ""
show_info "Setting up NFS server for K8s scratch storage..."

NFS_CONTAINER_NAME="backend-ai-test-nfs"
NFS_EXPORT_PATH="/export/backend-ai-scratch"
# Use multi-arch image that supports arm64 (maintained, supports linux/arm64)
NFS_IMAGE="ghcr.io/obeone/nfs-server:latest"

# Check if NFS container already exists
if $DOCKER_SUDO docker ps -a --format '{{.Names}}' | grep -q "^${NFS_CONTAINER_NAME}$"; then
  show_warn "Container $NFS_CONTAINER_NAME already exists"

  # Check if it's running
  if $DOCKER_SUDO docker ps --format '{{.Names}}' | grep -q "^${NFS_CONTAINER_NAME}$"; then
    show_info "NFS server is already running"
  else
    show_info "Starting existing NFS container..."
    $DOCKER_SUDO docker start $NFS_CONTAINER_NAME
    sleep 2
  fi
else
  show_info "Creating NFS server container..."

  # Create NFS data directory if it doesn't exist (use sudo for chmod if needed)
  if [ ! -d "/tmp/backend-ai-nfs-data" ]; then
    mkdir -p /tmp/backend-ai-nfs-data
  fi

  # Try to chmod, use sudo if regular chmod fails
  if ! chmod 777 /tmp/backend-ai-nfs-data 2>/dev/null; then
    sudo chmod 777 /tmp/backend-ai-nfs-data
  fi

  # Create NFS server container
  # Using NFS v4 only (port 2049) to avoid rpcbind conflicts on port 111
  $DOCKER_SUDO docker run -d \
    --name $NFS_CONTAINER_NAME \
    --privileged \
    -p 2049:2049 \
    -e NFS_VERSION=4 \
    -e NFS_EXPORT_0="$NFS_EXPORT_PATH *(rw,sync,no_subtree_check,no_root_squash,insecure,fsid=0)" \
    -v /tmp/backend-ai-nfs-data:$NFS_EXPORT_PATH:rw \
    $NFS_IMAGE

  show_info "✓ NFS server container created"
  sleep 3
fi

# Verify NFS is accessible
if command -v showmount &> /dev/null; then
  if showmount -e localhost 2>/dev/null | grep -q "$NFS_EXPORT_PATH"; then
    show_info "✓ NFS server is accessible"
  else
    show_warn "NFS exports not showing up yet, may need a moment to initialize"
  fi
else
  show_warn "showmount command not found, skipping NFS verification"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
show_info "Setup Complete! 🎉"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Running containers:"
$DOCKER_SUDO docker ps --filter "name=backend-ai-test" --format "  {{.Names}}: {{.Status}} ({{.Ports}})"
echo ""
show_info "Configuration Summary:"
echo "  - etcd: localhost:$ETCD_PORT (namespace: $ETCD_NAMESPACE)"
echo "  - Redis: localhost:$REDIS_PORT (K8s pods use: $HOST_IP:$REDIS_PORT)"
echo "  - NFS: $HOST_IP:$NFS_EXPORT_PATH"
echo ""
show_warn "MANUAL STEP REQUIRED:"
echo "  Edit deploy/kubernetes/agent-daemonset.yaml"
echo "  Update scratch-nfs-address to: $HOST_IP:$NFS_EXPORT_PATH"
echo ""
show_info "Next steps:"
echo "  1. Build and deploy: ./tools/setup-k8s-agent-test.sh"
echo "  2. Or see KUBERNETES-AGENT-TESTING.md for manual steps"
echo ""
show_info "Quick test (after deploying agent):"
echo "  # Terminal 1:"
echo "  kubectl port-forward -n backend-ai-test daemonset/backendai-agent 6001:6001"
echo ""
echo "  # Terminal 2:"
echo "  ipython"
echo "  >>> %run tools/example_repl_usage.py"
echo "  >>> await test_health()"
echo ""
show_info "Verify services:"
echo "  etcdctl --endpoints=localhost:$ETCD_PORT get /sorna/$ETCD_NAMESPACE/ --prefix"
echo "  showmount -e localhost"
echo ""
show_info "To stop and clean up:"
echo "  $DOCKER_SUDO docker stop $ETCD_CONTAINER_NAME $REDIS_CONTAINER_NAME $NFS_CONTAINER_NAME"
echo "  $DOCKER_SUDO docker rm $ETCD_CONTAINER_NAME $REDIS_CONTAINER_NAME $NFS_CONTAINER_NAME"
echo "  sudo rm -rf /tmp/backend-ai-nfs-data"
