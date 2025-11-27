# Kubernetes Agent Testing Guide

This guide provides a **complete, step-by-step walkthrough** for testing the Backend.AI Kubernetes agent with **GPU support** on NVIDIA hardware (tested on DGX Spark / GB10 ARM64).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start Summary](#quick-start-summary)
- [Step 1: Initialize Infrastructure Services](#step-1-initialize-infrastructure-services)
- [Step 2: Build and Deploy the Agent](#step-2-build-and-deploy-the-agent)
- [Step 3: Verify Agent Deployment](#step-3-verify-agent-deployment)
- [Step 4: Test Basic RPC Functions](#step-4-test-basic-rpc-functions)
- [Step 5: Create and Test GPU Kernels](#step-5-create-and-test-gpu-kernels)
- [Architecture Overview](#architecture-overview)
- [Configuration Reference](#configuration-reference)
- [Critical Assumptions and Manual Steps](#critical-assumptions-and-manual-steps)
- [Known Issues and Workarounds](#known-issues-and-workarounds)
- [Troubleshooting](#troubleshooting)
- [Useful Commands Cheatsheet](#useful-commands-cheatsheet)
- [Cleanup](#cleanup)
- [Files Reference](#files-reference)

---

## Prerequisites

### Hardware Requirements

- **NVIDIA GPU** (tested on GB10 / Grace Blackwell ARM64)
- Sufficient RAM (recommend 16GB+)
- Sufficient disk space for Docker images (~30GB for NGC PyTorch)

### Software Requirements (Must Be Pre-Installed)

The following must be set up BEFORE running this guide:

1. **Kubernetes Cluster** (k3s recommended for single-node testing)
   ```bash
   # Verify k3s is running
   kubectl cluster-info
   kubectl get nodes
   ```

2. **NVIDIA Container Toolkit** (installed and configured)
   ```bash
   # Verify NVIDIA runtime is available
   nvidia-ctk --version

   # Verify GPU is accessible via container runtime
   sudo docker run --rm --gpus all nvidia/cuda:12.2.2-base-ubuntu22.04 nvidia-smi
   ```

3. **NVIDIA Device Plugin for Kubernetes**
   ```bash
   # Verify device plugin is running
   kubectl get pods -n kube-system | grep nvidia

   # Verify GPU resources are advertised
   kubectl get nodes -o json | jq '.items[].status.allocatable["nvidia.com/gpu"]'
   ```

4. **NVIDIA RuntimeClass** (for k3s)
   ```bash
   # Verify RuntimeClass exists
   kubectl get runtimeclass nvidia

   # If not exists, create it:
   cat <<EOF | kubectl apply -f -
   apiVersion: node.k8s.io/v1
   kind: RuntimeClass
   metadata:
     name: nvidia
   handler: nvidia
   EOF
   ```

5. **Docker** (for building images and running infrastructure containers)
   ```bash
   docker --version
   ```

6. **etcdctl** (for etcd initialization)
   ```bash
   # Install if not available
   # On macOS: brew install etcd
   # On Ubuntu: sudo apt install etcd-client
   etcdctl version
   ```

7. **Python environment** with Backend.AI source
   ```bash
   # From the backend.ai repository root
   pants export --resolve=python-default
   ```

### Network Requirements

- Port 2479 available (isolated etcd)
- Port 6479 available (isolated Redis)
- Port 2049 available (NFS server)
- Port 30001 available (NodePort for agent RPC)
- Port 30003 available (NodePort for agent HTTP)

---

## Quick Start Summary

For those who know what they're doing:

```bash
# 1. Initialize etcd, Redis, NFS (from repo root)
./tools/init-standalone-k8s-test.sh

# 2. Edit the DaemonSet with your host IP (CRITICAL!)
vi deploy/kubernetes/agent-daemonset.yaml
# Change: ip: "10.100.66.2" to your actual host IP

# 3. Build and deploy agent
./deploy/kubernetes/quickstart.sh

# 4. Port forward for RPC access
kubectl port-forward -n backend-ai-test daemonset/backendai-agent 6001:6001

# 5. Test in another terminal
PYTHONPATH=src ipython
>>> %run tools/test_kernel_creation.py
>>> await test_create_gpu_kernel()
```

---

## Step 1: Initialize Infrastructure Services

### 1.1 Run the Initialization Script

```bash
cd /path/to/backend.ai
./tools/init-standalone-k8s-test.sh
```

This script automatically:
- Starts an **isolated etcd** container on port 2479
- Starts an **isolated Redis** container on port 6479
- Starts an **NFS server** container on port 2049
- Creates `/tmp/backend-ai-nfs-data` directory for scratch storage
- Initializes etcd with required configuration keys

### 1.2 Verify Services Are Running

```bash
# Check all containers are running
docker ps --filter "name=backend-ai-test"

# Expected output:
# backend-ai-test-etcd   ... Up ...   0.0.0.0:2479->2379/tcp
# backend-ai-test-redis  ... Up ...   0.0.0.0:6479->6379/tcp
# backend-ai-test-nfs    ... Up ...   0.0.0.0:2049->2049/tcp

# Verify etcd keys
export ETCDCTL_API=3
etcdctl --endpoints=localhost:2479 get /sorna/test-standalone/ --prefix

# Expected keys:
# /sorna/test-standalone/nodes/manager/test-manager -> "up"
# /sorna/test-standalone/config/redis/addr -> "<YOUR_HOST_IP>:6479"
# /sorna/test-standalone/config/redis/redis_helper_config/socket_timeout -> "5.0"
```

### 1.3 Note Your Host IP

The script outputs your host IP. **You will need this for the next step.**

```bash
# Get your host IP manually if needed
hostname -I | awk '{print $1}'
```

---

## Step 2: Build and Deploy the Agent

### 2.1 Update DaemonSet Configuration (CRITICAL MANUAL STEP)

Before deploying, you **MUST** update the host IP in the DaemonSet:

```bash
vi deploy/kubernetes/agent-daemonset.yaml
```

Find and update this section (around line 155-158):

```yaml
      hostAliases:
        - hostnames:
            - host.k8s.internal
          ip: "10.100.66.2"  # <-- CHANGE THIS to your host IP
```

Replace `10.100.66.2` with your actual host IP from Step 1.3.

### 2.2 Run the Quickstart Script

```bash
./deploy/kubernetes/quickstart.sh
```

This script:
1. Builds Python wheels using `pants package`
2. Builds the agent Docker image for your platform (ARM64/x86_64)
3. Imports the image into k3s containerd
4. Creates the `backend-ai-test` namespace
5. Deploys the ConfigMap, DaemonSet, ServiceAccount, RBAC, and NodePort Service

### 2.3 Alternative: Manual Build and Deploy

If the quickstart script fails, do it manually:

```bash
# Build wheels
./scripts/build-wheels.sh

# Build Docker image
docker build \
  --platform linux/arm64 \
  --file docker/agent/Dockerfile \
  --tag backendai-agent:latest \
  .

# Import to k3s
docker save backendai-agent:latest | sudo k3s ctr images import -

# Deploy
kubectl create namespace backend-ai-test --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/kubernetes/agent-daemonset.yaml
```

---

## Step 3: Verify Agent Deployment

### 3.1 Check Pod Status

```bash
kubectl get pods -n backend-ai-test
# Expected: backendai-agent-xxxxx   1/1   Running

kubectl get all -n backend-ai-test
```

### 3.2 Check Agent Logs

```bash
kubectl logs -n backend-ai-test -l app=backendai-agent -f
```

Look for:
- `"Agent starting..."`
- `"Connected to Redis"`
- `"CUDA devices found"` (if GPU is available)
- No error messages about etcd or Redis connectivity

### 3.3 Test Health Endpoint

```bash
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
curl http://$NODE_IP:30003/health
# Expected: {"status": "ok", ...}
```

### 3.4 Verify GPU Detection

Check agent logs for GPU detection:

```bash
kubectl logs -n backend-ai-test -l app=backendai-agent | grep -i cuda
```

You should see entries about CUDA device enumeration.

---

## Step 4: Test Basic RPC Functions

### 4.1 Set Up Port Forwarding

Open a dedicated terminal for port forwarding:

```bash
kubectl port-forward -n backend-ai-test daemonset/backendai-agent 6001:6001
```

Keep this terminal running.

### 4.2 Test RPC Connection

In another terminal:

```bash
cd /path/to/backend.ai
PYTHONPATH=src ipython
```

In IPython:

```python
# Load test utilities
%run tools/example_repl_usage.py

# Test health check
await test_health()

# Test hardware info (should show GPU if available)
await test_hwinfo()

# Test local config
await test_local_config()
```

---

## Step 5: Create and Test GPU Kernels

### 5.1 Update Test Configuration

Edit `tools/test_kernel_creation.py` to set your agent address:

```python
# Line 39 - Update to your NodePort address or use localhost with port-forward
AGENT_ADDR = "tcp://localhost:6001"  # If using port-forward
# OR
AGENT_ADDR = "tcp://10.100.66.2:30001"  # Direct NodePort access
```

### 5.2 Create a GPU Kernel

```python
# In IPython (PYTHONPATH=src ipython)
%run tools/test_kernel_creation.py

# Create kernel with GPU
result = await test_create_gpu_kernel()
# Note the session_id and kernel_id from output
```

### 5.3 Wait for Kernel Pod to Start

```bash
# In another terminal, watch kernel pods
kubectl get pods -n backend-ai-test -w

# Wait for kernel pod to show Running (may take a few minutes for image pull)
# The NGC PyTorch image is ~15GB, so first pull takes a while
```

### 5.4 Test GPU Access in Kernel

Once the kernel pod is Running:

```python
# In IPython - use the session_id and kernel_id from step 5.2
session_id = "your-session-id"
kernel_id = "your-kernel-id"

# Test PyTorch CUDA
result = await test_execute_code(
    session_id,
    kernel_id,
    "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
)

# Test nvidia-smi (run as batch mode for shell commands)
result = await test_execute_code(
    session_id,
    kernel_id,
    "!nvidia-smi",
    mode="query"
)

# Test CUDA device properties
result = await test_execute_code(
    session_id,
    kernel_id,
    """
import torch
if torch.cuda.is_available():
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Device name: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
"""
)
```

### 5.5 Clean Up Kernel

```python
await test_destroy_kernel(session_id, kernel_id)
```

---

## Architecture Overview

```
+-------------------+
|   K8s Cluster     |
|  +-------------+  |
|  | K8s Agent   |--+--+
|  |  DaemonSet  |  |  |
|  +-------------+  |  |
|                   |  |
|  +-------------+  |  |
|  |Kernel Pods  |  |  |
|  | (GPU access)|  |  |
|  +-------------+  |  |
+-------------------+  |
                       | RPC (tcp://:6001)
      +----------------+--------+
      |                         |
      v                         v
+----------+          +-----------------+
| Isolated |          |   Manager Stub  |
|  etcd    |          |  (IPython REPL) |
|  :2479   |<---------+                 |
+----------+          +-----------------+
      ^
      |
+-----+----+
| Isolated |
|  Redis   |
|  :6479   |
+----------+
      ^
      |
+-----+----+
|   NFS    |
|  Server  |
|  :2049   |
+----------+
      ^
      |
+-----+------------+
| /tmp/backend-ai- |
|   nfs-data/      |
| (scratch + krunner)|
+------------------+
```

**Key Points**:
- Agent runs as DaemonSet with NVML access (no GPU resource request)
- Kernel pods request `nvidia.com/gpu` for exclusive GPU access
- All infrastructure services run in Docker on the host (isolated from production)
- Scratch storage uses hostPath for single-node testing

---

## Configuration Reference

### Agent DaemonSet Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `etcd.addr.port` | 2479 | Isolated etcd instance |
| `etcd.namespace` | test-standalone | Separate from production |
| `agent.backend` | kubernetes | Enable K8s backend |
| `container.scratch-type` | hostdir | Use host filesystem |
| `container.scratch-root` | /tmp/backend-ai-nfs-data | Scratch storage path |
| `runtimeClassName` | nvidia | Use NVIDIA container runtime |

### Required etcd Keys

| Key | Value | Purpose |
|-----|-------|---------|
| `/sorna/test-standalone/nodes/manager/test-manager` | `"up"` | Mock manager presence |
| `/sorna/test-standalone/config/redis/addr` | `"HOST_IP:6479"` | Redis connection |
| `/sorna/test-standalone/config/redis/redis_helper_config/socket_timeout` | `"5.0"` | Redis timeout |

### Environment Variables (Set by DaemonSet)

| Variable | Source | Purpose |
|----------|--------|---------|
| `POD_NAMESPACE` | fieldRef | Namespace for kernel pods |
| `NODE_NAME` | fieldRef | Node name for scheduling |
| `NODE_IP` | fieldRef | Node IP for networking |
| `NVIDIA_VISIBLE_DEVICES` | Static: "all" | NVML access for agent |

---

## Critical Assumptions and Manual Steps

### Things You MUST Do Manually

1. **Update hostAliases IP in DaemonSet**
   - File: `deploy/kubernetes/agent-daemonset.yaml`
   - Line ~158: Change `ip: "10.100.66.2"` to your actual host IP
   - **Why**: K8s pods need to reach etcd/Redis on host via `host.k8s.internal`

2. **Update AGENT_ADDR in test scripts**
   - File: `tools/test_kernel_creation.py` line 39
   - File: `tools/example_repl_usage.py` line 22
   - Set to `tcp://localhost:6001` (with port-forward) or `tcp://HOST_IP:30001`

### Implicit Assumptions in Scripts

#### `init-standalone-k8s-test.sh`
- Assumes `hostname -I` returns the primary network interface IP first
- Assumes ports 2479, 6479, 2049 are available
- Assumes Docker is installed and accessible (tries sudo if needed)
- Assumes `etcdctl` is installed for verification
- Creates `/tmp/backend-ai-nfs-data` with 777 permissions (may need sudo)

#### `quickstart.sh`
- Detects cluster type via kubectl node JSON (may not detect all k3s installations)
- Falls back to `k3s` binary detection if JSON detection fails
- Assumes `build-agent-image.sh` exists and works
- Waits 120s for agent to be ready

#### `build-agent-image.sh`
- Defaults to `linux/arm64` platform (change `PLATFORM` env var for x86_64)
- Runs `build-wheels.sh` first (requires pants to be set up)
- Auto-loads to k3s if detected

#### `agent-daemonset.yaml`
- Uses `imagePullPolicy: Never` (expects local image)
- Hardcodes scratch-root to `/tmp/backend-ai-nfs-data`
- Requires `nvidia` RuntimeClass to exist
- Mounts Docker socket (not used but kept for compatibility)

#### Kernel Creation (`test_kernel_creation.py`)
- Hardcoded to use NGC PyTorch image `nvcr.io/nvidia/pytorch:24.08-py3`
- Assumes ARM64 architecture (change `architecture` for x86_64)
- First kernel creation pulls ~15GB image (takes several minutes)

### File Paths That Must Exist

| Path | Created By | Purpose |
|------|------------|---------|
| `/tmp/backend-ai-nfs-data` | init-standalone-k8s-test.sh | Scratch storage root |
| `/tmp/backend-ai-nfs-data/runner/` | Agent (copy_runner_files) | Krunner helper files |
| `/tmp/backend-ai-nfs-data/backendai-krunner.v*.*.*` | Agent (prepare_krunner_env) | Krunner environment |
| `/tmp/backend-ai-nfs-data/<kernel-id>/work` | Agent (prepare_scratch) | Kernel work directory |
| `/tmp/backend-ai-nfs-data/<kernel-id>/config` | Agent (prepare_scratch) | Kernel config directory |

---

## Known Issues and Workarounds

### 1. Jupyter Kernelspec Issue with Third-Party Images

**Problem**: Third-party images (like NGC PyTorch) have kernelspecs with relative Python paths (`python` instead of `/usr/bin/python`), causing IPython kernel launch to fail.

**Symptom**: Kernel logs show:
```
PermissionError: [Errno 13] Permission denied: ''
```
or
```
['', '-m', 'ipykernel_launcher', '-f', ...]
```

**Fix**: Already fixed in `src/ai/backend/kernel/base.py`. The kernel now creates a custom kernelspec at `/tmp/backendai-kernelspec/python3/kernel.json` with the explicit runtime path.

**Manual Workaround** (if using old kernel code): Copy the updated `base.py` to the scratch directory:
```bash
cp src/ai/backend/kernel/base.py /tmp/backend-ai-nfs-data/kernel/
```

### 2. Empty Container ID in Logs

**Symptom**: Agent logs show `detected active containers: ['']`

**Cause**: Fixed in `src/ai/backend/agent/kubernetes/agent.py`. Container ID now uses pod UID.

**Impact**: Cosmetic only, does not affect functionality.

### 3. ttyd Service Not Starting

**Symptom**: Kernel logs show:
```
python-kernel: [WARNING] failed to start service ttyd: the executable file is not found: /opt/kernel/ttyd
```

**Cause**: ttyd binary filename includes architecture suffix but symlink logic doesn't match perfectly.

**Impact**: Minor - only affects web terminal feature. SSH works fine.

### 4. PyTorch Compute Capability Warning (GB10)

**Symptom**: When running PyTorch on GB10:
```
UserWarning: NVIDIA GB10 with CUDA capability sm_121 is not compatible with the current PyTorch installation. The current PyTorch install supports CUDA capabilities sm_50 sm_60 sm_61 sm_70 sm_75 sm_80 sm_86 sm_90.
```

**Cause**: GB10's compute capability (sm_121) is newer than PyTorch 24.08's support.

**Impact**: PyTorch still works but may not use all GPU features. `torch.cuda.is_available()` returns True.

### 5. Large Image Pull Times

**Symptom**: Kernel pod stuck in `Init:0/1` or `ContainerCreating` for several minutes.

**Cause**: NGC PyTorch image is ~15GB.

**Workaround**: Pre-pull the image:
```bash
sudo k3s ctr images pull nvcr.io/nvidia/pytorch:24.08-py3
```

---

## Troubleshooting

### Agent Pod Won't Start

```bash
# Check pod status
kubectl describe pod -n backend-ai-test -l app=backendai-agent

# Check logs
kubectl logs -n backend-ai-test -l app=backendai-agent --previous

# Common issues:
# 1. Can't reach etcd: Check hostAliases IP is correct
# 2. Can't reach Redis: Check Redis is bound to 0.0.0.0 (not just localhost)
# 3. Missing RuntimeClass: Create nvidia RuntimeClass
```

### Agent Can't Connect to etcd/Redis

```bash
# Test from inside agent pod
kubectl exec -it -n backend-ai-test daemonset/backendai-agent -- bash

# Inside pod:
nc -zv host.k8s.internal 2479  # etcd
nc -zv host.k8s.internal 6479  # Redis

# If fails, verify hostAliases IP and host firewall
```

### Kernel Pod Fails to Start

```bash
# Check kernel pod events
kubectl describe pod -n backend-ai-test <kernel-pod-name>

# Check kernel logs
kubectl logs -n backend-ai-test <kernel-pod-name>

# Common issues:
# 1. Image pull failure: Check image name and registry access
# 2. GPU not available: Check nvidia.com/gpu resources on node
# 3. PVC not bound: Check scratch PV/PVC status
```

### GPU Not Detected by Agent

```bash
# Check NVML access in agent pod
kubectl exec -it -n backend-ai-test daemonset/backendai-agent -- \
  python3 -c "import ctypes; nvml = ctypes.CDLL('libnvidia-ml.so.1'); print('NVML loaded')"

# Verify NVIDIA_VISIBLE_DEVICES is set
kubectl exec -it -n backend-ai-test daemonset/backendai-agent -- env | grep NVIDIA
```

### Code Execution Returns Empty Result

```bash
# Check kernel is actually running
kubectl get pods -n backend-ai-test -l ai.backend.kernel-id

# Check kernel logs for errors
kubectl logs -n backend-ai-test <kernel-pod-name>

# Verify the kernel's Jupyter kernel is started (look for "starting python3 kernel")
```

---

## Useful Commands Cheatsheet

### Agent Management

```bash
# Watch agent logs (last 3000 lines, follow)
kubectl logs -n backend-ai-test -l app=backendai-agent --tail=3000 -f

# Redeploy agent after config changes
kubectl apply -f deploy/kubernetes/agent-daemonset.yaml

# Full reset: delete and recreate agent
kubectl delete -f deploy/kubernetes/agent-daemonset.yaml
kubectl apply -f deploy/kubernetes/agent-daemonset.yaml
```

### Kernel Pod Management

```bash
# List all pods in test namespace
kubectl -n backend-ai-test get pods

# Get kernel pod logs (filtering out noisy libbaihook messages)
kubectl -n backend-ai-test logs $(kubectl -n backend-ai-test get pods -o name | grep kernel- | head -1) | grep -v "/opt/kernel/libbaihook.so"

# Describe kernel pod (useful for debugging scheduling/resource issues)
kubectl -n backend-ai-test describe pod <kernel-pod-name>

# Delete all kernel deployments (cleanup orphaned kernels)
kubectl -n backend-ai-test delete deployment --all
```

### IPython REPL Testing

```bash
# Start IPython with correct path
PYTHONPATH=src/ ipython
```

```python
# Import test utilities
import asyncio
from tools.agent_rpc_client import StandaloneAgentClient
from tools.test_kernel_creation import (
    test_create_simple_kernel,
    test_create_gpu_kernel,
    test_destroy_kernel,
    test_execute_code,
    test_check_gpu,
    test_full_lifecycle,
)

# Create a GPU kernel
res = asyncio.run(test_create_gpu_kernel())
# Note the session_id and kernel_id from output

# Create a CPU-only kernel
res = asyncio.run(test_create_simple_kernel())

# Execute code and print result
res = asyncio.run(test_execute_code(
    session_id="YOUR-SESSION-ID",
    kernel_id="YOUR-KERNEL-ID",
    code="import torch; print(torch.cuda.is_available())"
))
print(res["console"][0][1])

# Run nvidia-smi
res = asyncio.run(test_execute_code(
    session_id="YOUR-SESSION-ID",
    kernel_id="YOUR-KERNEL-ID",
    code="!nvidia-smi"
))
print(res["console"][0][1])

# Destroy kernel when done
asyncio.run(test_destroy_kernel(
    session_id="YOUR-SESSION-ID",
    kernel_id="YOUR-KERNEL-ID"
))
```

### Quick Test Workflow

```bash
# Terminal 1: Port forward (keep running)
kubectl port-forward -n backend-ai-test daemonset/backendai-agent 6001:6001

# Terminal 2: Watch pods
kubectl -n backend-ai-test get pods -w

# Terminal 3: IPython testing
PYTHONPATH=src/ ipython
```

---

## Cleanup

### Remove K8s Resources

```bash
kubectl delete namespace backend-ai-test
```

### Remove Docker Containers

```bash
docker stop backend-ai-test-etcd backend-ai-test-redis backend-ai-test-nfs
docker rm backend-ai-test-etcd backend-ai-test-redis backend-ai-test-nfs
```

### Remove Scratch Data

```bash
sudo rm -rf /tmp/backend-ai-nfs-data
```

### Remove k3s Images (Optional)

```bash
sudo k3s ctr images rm docker.io/library/backendai-agent:latest
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `tools/init-standalone-k8s-test.sh` | Initialize etcd/Redis/NFS containers |
| `deploy/kubernetes/quickstart.sh` | Automated build and deployment |
| `deploy/kubernetes/agent-daemonset.yaml` | Complete K8s manifests (ConfigMap, DaemonSet, RBAC, Service) |
| `scripts/build-agent-image.sh` | Build agent Docker image |
| `scripts/build-wheels.sh` | Build Python wheels with Pants |
| `docker/agent/Dockerfile` | Agent container definition |
| `tools/agent_rpc_client.py` | Python RPC client for testing |
| `tools/test_kernel_creation.py` | Kernel creation test script |
| `tools/example_repl_usage.py` | IPython REPL usage examples |
| `src/ai/backend/runner/entrypoint.sh` | Kernel pod entrypoint (creates symlinks) |
| `src/ai/backend/kernel/base.py` | Kernel runner base class (includes kernelspec fix) |
| `src/ai/backend/agent/kubernetes/agent.py` | K8s agent implementation |
| `src/ai/backend/agent/kubernetes/kernel.py` | K8s kernel lifecycle management |

---

## Summary

### Minimal Requirements
1. k3s cluster with NVIDIA Container Toolkit + Device Plugin
2. etcd container on port 2479
3. Redis container on port 6479
4. Scratch directory at `/tmp/backend-ai-nfs-data`

### Critical Manual Steps
1. Update `hostAliases` IP in `agent-daemonset.yaml`
2. Update `AGENT_ADDR` in test scripts

### What Success Looks Like
1. Agent pod Running with no error logs
2. `await test_health()` returns `{"status": "ok"}`
3. `await test_create_gpu_kernel()` creates kernel pod
4. Kernel pod reaches Running state
5. `torch.cuda.is_available()` returns `True` in kernel
6. `!nvidia-smi` shows GPU in kernel
