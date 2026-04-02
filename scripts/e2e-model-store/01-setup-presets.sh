#!/bin/bash
# Scenario A: Create runtime variant presets and deployment revision preset.
#
# Prerequisites: source 00-env.sh
# Creates:
#   - Runtime variant presets for vLLM (tensor-parallel, gpu-mem-util)
#   - Deployment revision preset (vllm-4gpu-default)

set -euo pipefail
source "$(dirname "$0")/00-env.sh"

echo "--- A-1: Create runtime variant presets for vLLM ---"

TP_PRESET=$(./bai admin runtime-variant-preset create "{
  \"runtime_variant_id\": \"$VLLM_VARIANT_ID\",
  \"name\": \"e2e-tensor-parallel-size\",
  \"preset_target\": \"env\",
  \"value_type\": \"int\",
  \"default_value\": \"1\",
  \"key\": \"VLLM_TENSOR_PARALLEL_SIZE\"
}" 2>&1)
TP_PRESET_ID=$(echo "$TP_PRESET" | python3 -c "import sys,json; print(json.load(sys.stdin)['preset']['id'])")
echo "  Created: tensor-parallel-size preset ($TP_PRESET_ID)"

GPU_MEM_PRESET=$(./bai admin runtime-variant-preset create "{
  \"runtime_variant_id\": \"$VLLM_VARIANT_ID\",
  \"name\": \"e2e-gpu-memory-utilization\",
  \"preset_target\": \"args\",
  \"value_type\": \"float\",
  \"default_value\": \"0.9\",
  \"key\": \"--gpu-memory-utilization\"
}" 2>&1)
GPU_MEM_PRESET_ID=$(echo "$GPU_MEM_PRESET" | python3 -c "import sys,json; print(json.load(sys.stdin)['preset']['id'])")
echo "  Created: gpu-memory-utilization preset ($GPU_MEM_PRESET_ID)"

echo ""
echo "--- A-2: Create deployment revision preset (vllm-4gpu) ---"

REV_PRESET=$(./bai admin deployment revision-preset create "{
  \"runtime_variant_id\": \"$VLLM_VARIANT_ID\",
  \"name\": \"e2e-vllm-4gpu\",
  \"description\": \"vLLM 4 GPU default configuration for E2E test\",
  \"image\": \"$IMAGE_ID\",
  \"resource_slots\": [
    {\"resource_type\": \"cpu\", \"quantity\": \"8\"},
    {\"resource_type\": \"mem\", \"quantity\": \"32g\"},
    {\"resource_type\": \"cuda.device\", \"quantity\": \"4\"}
  ],
  \"resource_opts\": [{\"name\": \"shmem\", \"value\": \"16g\"}],
  \"environ\": [{\"key\": \"VLLM_TENSOR_PARALLEL_SIZE\", \"value\": \"4\"}],
  \"cluster_mode\": \"single-node\",
  \"cluster_size\": 1,
  \"preset_values\": [
    {\"preset_id\": \"$TP_PRESET_ID\", \"value\": \"4\"},
    {\"preset_id\": \"$GPU_MEM_PRESET_ID\", \"value\": \"0.9\"}
  ]
}" 2>&1)
REV_PRESET_ID=$(echo "$REV_PRESET" | python3 -c "import sys,json; print(json.load(sys.stdin)['preset']['id'])")
echo "  Created: vllm-4gpu revision preset ($REV_PRESET_ID)"

echo ""
echo "--- A-3: Create CPU-only preset with health check (for E2E route testing) ---"

CPU_PRESET=$(./bai admin deployment revision-preset create "{
  \"runtime_variant_id\": \"$VLLM_VARIANT_ID\",
  \"name\": \"e2e-cpu-healthcheck\",
  \"description\": \"CPU-only preset with serve.py health check for E2E testing\",
  \"image\": \"$IMAGE_ID\",
  \"resource_slots\": [
    {\"resource_type\": \"cpu\", \"quantity\": \"1\"},
    {\"resource_type\": \"mem\", \"quantity\": \"1g\"}
  ],
  \"startup_command\": \"python /models/serve.py\",
  \"model_definition\": {
    \"models\": [{
      \"name\": \"test-model\",
      \"model_path\": \"/models\",
      \"service\": {
        \"start_command\": \"python /models/serve.py\",
        \"port\": 8000,
        \"health_check\": {
          \"path\": \"/health\",
          \"interval\": 5,
          \"max_retries\": 3,
          \"expected_status_code\": 200
        }
      }
    }]
  },
  \"cluster_mode\": \"single-node\",
  \"cluster_size\": 1
}" 2>&1)
CPU_PRESET_ID=$(echo "$CPU_PRESET" | python3 -c "import sys,json; print(json.load(sys.stdin)['preset']['id'])")
echo "  Created: cpu-healthcheck preset ($CPU_PRESET_ID)"

# Export for subsequent scripts
export TP_PRESET_ID GPU_MEM_PRESET_ID REV_PRESET_ID CPU_PRESET_ID

echo ""
echo "--- Setup complete ---"
echo "  TP_PRESET_ID:      $TP_PRESET_ID"
echo "  GPU_MEM_PRESET_ID: $GPU_MEM_PRESET_ID"
echo "  REV_PRESET_ID:     $REV_PRESET_ID"
echo "  CPU_PRESET_ID:     $CPU_PRESET_ID"
