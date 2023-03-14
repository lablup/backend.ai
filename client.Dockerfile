ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
RUN pip wheel --wheel-dir=/wheels --no-cache-dir backend.ai-client

FROM python:${PYTHON_VERSION}
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl
