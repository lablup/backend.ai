#!/bin/sh
# Derive distributed training environment variables from BACKENDAI_* cluster variables.
#
# This script is sourced (not executed) during container initialization.
# It sets MASTER_ADDR and MASTER_PORT for distributed training coordination,
# using the BACKENDAI_* cluster variables that are already injected by the manager.
#
# WORLD_SIZE, RANK, and LOCAL_RANK are intentionally NOT set here — launchers
# like torchrun and TensorFlow's MultiWorkerMirroredStrategy set these per-process
# based on the number of GPUs per node. Pre-setting them at the container level
# would conflict with multi-GPU-per-node setups.
#
# The variables are only exported when a cluster session has more than one container
# (BACKENDAI_CLUSTER_SIZE > 1), so single-container sessions are unaffected.
#
# Users can override any derived variable by setting it before this script runs
# (e.g., via session environ).

if [ -z "$BACKENDAI_CLUSTER_SIZE" ] || [ "$BACKENDAI_CLUSTER_SIZE" -le 1 ] 2>/dev/null; then
  return 0 2>/dev/null || exit 0
fi

# --- PyTorch / General distributed training ---
# Only set MASTER_ADDR and MASTER_PORT — the two variables that launchers like
# torchrun cannot auto-discover and that require cluster-level knowledge.
# WORLD_SIZE, RANK, LOCAL_RANK are left to the launcher (e.g., torchrun --nproc_per_node).
if [ -z "$MASTER_ADDR" ]; then
  export MASTER_ADDR="$(echo "$BACKENDAI_CLUSTER_HOSTS" | cut -d, -f1)"
fi
if [ -z "$MASTER_PORT" ]; then
  export MASTER_PORT="${BACKENDAI_DIST_MASTER_PORT:-29500}"
fi

# --- TensorFlow TF_CONFIG ---
# https://www.tensorflow.org/guide/distributed_training#setting_up_the_tf_config_environment_variable
# Each worker gets a unique port derived from the base port + its rank to avoid
# port conflicts when multiple workers run on the same host.
if [ -z "$TF_CONFIG" ]; then
  _DIST_BASE_PORT="${BACKENDAI_DIST_MASTER_PORT:-29500}"
  _TF_WORKER_LIST=""
  _TF_WORKER_IDX=0
  _OLD_IFS="$IFS"
  IFS=','
  for _host in $BACKENDAI_CLUSTER_HOSTS; do
    if [ -n "$_TF_WORKER_LIST" ]; then
      _TF_WORKER_LIST="${_TF_WORKER_LIST},"
    fi
    _TF_WORKER_PORT=$((_DIST_BASE_PORT + _TF_WORKER_IDX))
    _TF_WORKER_LIST="${_TF_WORKER_LIST}\"${_host}:${_TF_WORKER_PORT}\""
    _TF_WORKER_IDX=$((_TF_WORKER_IDX + 1))
  done
  IFS="$_OLD_IFS"

  export TF_CONFIG="{\"cluster\":{\"worker\":[${_TF_WORKER_LIST}]},\"task\":{\"type\":\"worker\",\"index\":${BACKENDAI_CLUSTER_LOCAL_RANK:-0}}}"

  unset _DIST_BASE_PORT _TF_WORKER_LIST _TF_WORKER_IDX _TF_WORKER_PORT _OLD_IFS _host
fi
