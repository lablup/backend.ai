#!/bin/sh
# Derive distributed training environment variables from BACKENDAI_* cluster variables.
#
# This script is sourced (not executed) during container initialization.
# It sets framework-specific environment variables for PyTorch and TensorFlow
# distributed training, using the BACKENDAI_* cluster variables that are already
# injected by the manager.
#
# The variables are only exported when a cluster session has more than one container
# (BACKENDAI_CLUSTER_SIZE > 1), so single-container sessions are unaffected.
#
# Users can override any derived variable by setting it before this script runs
# (e.g., via session environ).

if [ -z "$BACKENDAI_CLUSTER_SIZE" ] || [ "$BACKENDAI_CLUSTER_SIZE" -le 1 ] 2>/dev/null; then
  return 0 2>/dev/null || exit 0
fi

DIST_MASTER_PORT="${BACKENDAI_DIST_MASTER_PORT:-29500}"
DIST_MASTER_ADDR="$(echo "$BACKENDAI_CLUSTER_HOSTS" | cut -d, -f1)"

# --- PyTorch distributed training variables ---
# https://pytorch.org/docs/stable/distributed.html#environment-variable-initialization
if [ -z "$WORLD_SIZE" ]; then
  export WORLD_SIZE="$BACKENDAI_CLUSTER_SIZE"
fi
if [ -z "$RANK" ]; then
  export RANK="$BACKENDAI_CLUSTER_LOCAL_RANK"
fi
if [ -z "$LOCAL_RANK" ]; then
  export LOCAL_RANK="$BACKENDAI_CLUSTER_LOCAL_RANK"
fi
if [ -z "$MASTER_ADDR" ]; then
  export MASTER_ADDR="$DIST_MASTER_ADDR"
fi
if [ -z "$MASTER_PORT" ]; then
  export MASTER_PORT="$DIST_MASTER_PORT"
fi

# --- TensorFlow TF_CONFIG ---
# https://www.tensorflow.org/guide/distributed_training#setting_up_the_tf_config_environment_variable
if [ -z "$TF_CONFIG" ]; then
  # Build the worker list: "host1:port","host2:port",...
  TF_WORKER_LIST=""
  IFS=','
  for host in $BACKENDAI_CLUSTER_HOSTS; do
    if [ -n "$TF_WORKER_LIST" ]; then
      TF_WORKER_LIST="${TF_WORKER_LIST},"
    fi
    TF_WORKER_LIST="${TF_WORKER_LIST}\"${host}:${DIST_MASTER_PORT}\""
  done
  unset IFS

  export TF_CONFIG="{\"cluster\":{\"worker\":[${TF_WORKER_LIST}]},\"task\":{\"type\":\"worker\",\"index\":${BACKENDAI_CLUSTER_LOCAL_RANK}}}"
fi

echo "Distributed training environment configured (cluster size: $BACKENDAI_CLUSTER_SIZE, rank: $RANK)"
