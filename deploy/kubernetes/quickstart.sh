#!/bin/bash
# Quick deployment script for Backend.AI Kubernetes Agent (Standalone Testing)
# This script deploys the agent on a K8s cluster using isolated testing services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "======================================================================"
echo "Backend.AI Kubernetes Agent - Quickstart Deployment"
echo "======================================================================"
echo ""
echo "This script will deploy the Backend.AI agent on your K8s cluster"
echo "using ISOLATED testing services to avoid conflicts with production."
echo ""
echo "Required services (must be running on host):"
echo "  - etcd on port 2479"
echo "  - Redis on port 6479"
echo ""
echo "Run tools/init-standalone-k8s-test.sh first if you haven't already!"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster"
    echo "Make sure your kubeconfig is set up correctly"
    exit 1
fi

echo "Connected to Kubernetes cluster:"
kubectl cluster-info | head -1
echo ""

# Create namespace
echo "Creating namespace 'backend-ai-test'..."
kubectl create namespace backend-ai-test --dry-run=client -o yaml | kubectl apply -f -

# Build agent image
echo ""
echo "Building agent Docker image..."
if [ ! -f "$PROJECT_ROOT/scripts/build-agent-image.sh" ]; then
    echo "ERROR: build-agent-image.sh not found at $PROJECT_ROOT/scripts/"
    exit 1
fi

cd "$PROJECT_ROOT"
bash scripts/build-agent-image.sh

# Load image into cluster (for kind/minikube)
echo ""
echo "Loading image into cluster..."
CLUSTER_TYPE=""

# Detect cluster type
if kubectl get nodes -o json | grep -q "kind://"; then
    CLUSTER_TYPE="kind"
    echo "Detected kind cluster"
    kind load docker-image backendai-agent:latest
elif kubectl get nodes -o json | grep -q "minikube"; then
    CLUSTER_TYPE="minikube"
    echo "Detected minikube cluster"
    # For minikube, use the docker daemon inside minikube
    echo "Note: Make sure you ran 'eval \$(minikube docker-env)' before building the image"
elif kubectl get nodes -o json | grep -qE "k3s|k3s.io"; then
    CLUSTER_TYPE="k3s"
    echo "Detected k3s cluster"
    # For k3s, import image from Docker to containerd
    echo "Importing Docker image to k3s..."
    docker save backendai-agent:latest | sudo k3s ctr images import -
    echo "Image imported to k3s"
elif command -v k3s &> /dev/null; then
    # Fallback: check if k3s binary exists
    CLUSTER_TYPE="k3s"
    echo "Detected k3s (via binary detection)"
    echo "Importing Docker image to k3s..."
    docker save backendai-agent:latest | sudo k3s ctr images import -
    echo "Image imported to k3s"
else
    echo "WARNING: Could not detect cluster type (kind/minikube/k3s)"
    echo "If using k3s, you may need to manually import the image:"
    echo "  docker save backendai-agent:latest | sudo k3s ctr images import -"
    echo ""
    echo "Press Ctrl+C to cancel or Enter to continue..."
    read
fi

# Get node IP for advertised-rpc-addr
echo ""
echo "Getting node IP for external access..."
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
if [ -z "$NODE_IP" ]; then
    echo "ERROR: Could not detect node IP"
    exit 1
fi
echo "Node IP: $NODE_IP"
echo ""
echo "NOTE: The agent will be accessible at:"
echo "  - RPC: $NODE_IP:30001"
echo "  - HTTP: $NODE_IP:30003"
echo ""

# Deploy agent
echo "Deploying agent DaemonSet..."
kubectl apply -f "$SCRIPT_DIR/agent-daemonset.yaml"

# Wait for agent to be ready
echo ""
echo "Waiting for agent pods to be ready..."
kubectl wait --for=condition=ready pod -l app=backendai-agent -n backend-ai-test --timeout=120s || true

# Show status
echo ""
echo "======================================================================"
echo "Deployment Status"
echo "======================================================================"
echo ""
kubectl get all -n backend-ai-test
echo ""

# Show logs
echo "======================================================================"
echo "Recent Agent Logs"
echo "======================================================================"
echo ""
kubectl logs -n backend-ai-test -l app=backendai-agent --tail=20 --all-containers=true || echo "No logs yet"
echo ""

# Show next steps
echo "======================================================================"
echo "Next Steps"
echo "======================================================================"
echo ""
echo "1. Check agent status:"
echo "   kubectl get pods -n backend-ai-test"
echo ""
echo "2. View agent logs:"
echo "   kubectl logs -n backend-ai-test -l app=backendai-agent -f"
echo ""
echo "3. Test agent RPC connection from host:"
echo "   cd tools"
echo "   python agent_rpc_client.py"
echo "   # Then in the REPL:"
echo "   await agent.ping()"
echo ""
echo "4. Check agent health endpoint:"
echo "   curl http://$NODE_IP:30003/health"
echo ""
echo "5. To delete the deployment:"
echo "   kubectl delete namespace backend-ai-test"
echo ""
echo "======================================================================"
echo "Deployment Complete!"
echo "======================================================================"
