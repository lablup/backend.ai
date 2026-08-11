# Build context MUST be the repository root (the paths below are context-relative):
#   docker build -f docker/backend.ai-base.dockerfile --build-arg PYTHON_VERSION=<ver> --build-arg PKGVER=<ver> .
ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION} AS builder
ARG PKGVER

# Install dependencies from requirements.txt to respect version constraints
COPY ./requirements.txt /requirements.txt
RUN pip wheel --wheel-dir=/wheels --no-cache-dir -r /requirements.txt

# Install the backend.ai packages from /dist (these are not in
# requirements.txt).  Resolving them JOINTLY with -r requirements.txt keeps
# the dependency versions consistent with the step above by construction
# (`-c` would be the usual tool, but pip rejects constraints entries carrying
# extras, which requirements.txt has); the step above still exists so the
# heavy dependency download is a layer that caches independently of dist/,
# and --find-links=/wheels lets this resolve reuse its wheels.
COPY ./dist /dist
RUN pip wheel --wheel-dir=/wheels --no-cache-dir \
    --find-links=/wheels --find-links=/dist \
    -r /requirements.txt \
    backend.ai-manager==${PKGVER} \
    backend.ai-agent==${PKGVER} \
    backend.ai-webserver==${PKGVER} \
    backend.ai-storage-proxy==${PKGVER} \
    backend.ai-client==${PKGVER} \
    backend.ai-appproxy-coordinator==${PKGVER} \
    backend.ai-appproxy-worker==${PKGVER}

FROM python:${PYTHON_VERSION}
ENV PYTHONUNBUFFERED=1
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*.whl
