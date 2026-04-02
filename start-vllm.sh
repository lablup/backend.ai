#! /bin/bash
EXTRA_ARGS=""

if [[ ! -z "$VLLM_QUANTIZATION" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS --quantization $VLLM_QUANTIAZATION"
fi
if [[ ! -z "$VLLM_TP_SIZE" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS --tensor-parallel-size $VLLM_TP_SIZE"
fi
if [[ ! -z "$VLLM_PP_SIZE" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS --tensor-parallel-size $VLLM_PP_SIZE"
fi
if [[ ! -z "$VLLM_EXTRA_ARGS" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS $VLLM_EXTRA_ARGS"
fi

python -m vllm.entrypoints.openai.api_server \
    --model /models \
    --served-model-name $BACKEND_MODEL_NAME \
    --host 0.0.0.0 \
    --port 8000 \
    $EXTRA_ARGS
