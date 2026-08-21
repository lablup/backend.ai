# Bake definition for the published lablup/backend.ai-* service images.
#
# All seven service dockerfiles start FROM the shared (unpublished) base image
# backend.ai-base:${PKGVER}, which installs every backend.ai package once.
# The `contexts` wiring below resolves that FROM reference to the `base`
# target inside the same build, so the base never needs to exist in a
# registry or the local image store — bake builds it (per platform) and feeds
# it to the service targets.
#
# CI (.github/workflows/docker-images.yml) runs the `default` group with
# --push.  Local usage:
#   PKGVER=$(python3 scripts/normalize-version.py "$(cat VERSION)") \
#   PYTHON_VERSION=<ver from pants.toml> \
#   docker buildx bake backend.ai-manager --set '*.platform=linux/arm64' --load
#
# The service target names MUST stay in sync with PUBLISHABLE_SERVICES in
# scripts/list-dockerfiles.sh — the workflow's prepare job fails on drift.

variable "PYTHON_VERSION" {
  default = ""
}
variable "PKGVER" {
  default = ""
}
variable "REGISTRY" {
  default = "lablup"
}
# Set to true only for final (non-prerelease) releases; moves the `latest` tag.
variable "TAG_LATEST" {
  default = false
}
variable "REVISION" {
  default = ""
}

group "default" {
  targets = [
    "backend_ai-manager",
    "backend_ai-agent",
    "backend_ai-webserver",
    "backend_ai-storage-proxy",
    "backend_ai-client",
    "backend_ai-appproxy-coordinator",
    "backend_ai-appproxy-worker",
  ]
}

# Shared base image: built as a dependency of the service targets, never
# pushed.  Carries all backend.ai packages so the service layers are thin and
# every image shares the same (cacheable) heavy layer.
target "base" {
  context    = "."
  dockerfile = "docker/backend.ai-base.dockerfile"
  args = {
    PYTHON_VERSION = PYTHON_VERSION
    PKGVER         = PKGVER
  }
  platforms  = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=gha,scope=backend.ai-base"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-base"]
}

target "_service" {
  context = "."
  args = {
    PKGVER = PKGVER
  }
  contexts = {
    "backend.ai-base:${PKGVER}" = "target:base"
  }
  platforms = ["linux/amd64", "linux/arm64"]
  attest = [
    "type=provenance,mode=max",
    "type=sbom",
  ]
  labels = {
    "org.opencontainers.image.source"   = "https://github.com/lablup/backend.ai"
    "org.opencontainers.image.version"  = PKGVER
    "org.opencontainers.image.revision" = REVISION
  }
}

# One target per published image.  Target names use `_` in place of the `.`
# of the image name (bake target names cannot contain dots); the drift check
# in the workflow maps them back.
target "backend_ai-manager" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-manager.Dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-manager:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-manager:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-manager"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-manager"]
}

target "backend_ai-agent" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-agent.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-agent:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-agent:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-agent"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-agent"]
}

target "backend_ai-webserver" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-webserver.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-webserver:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-webserver:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-webserver"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-webserver"]
}

target "backend_ai-storage-proxy" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-storage-proxy.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-storage-proxy:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-storage-proxy:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-storage-proxy"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-storage-proxy"]
}

target "backend_ai-client" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-client.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-client:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-client:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-client"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-client"]
}

target "backend_ai-appproxy-coordinator" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-appproxy-coordinator.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-appproxy-coordinator:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-appproxy-coordinator:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-appproxy-coordinator"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-appproxy-coordinator"]
}

target "backend_ai-appproxy-worker" {
  inherits   = ["_service"]
  dockerfile = "docker/backend.ai-appproxy-worker.dockerfile"
  tags = concat(
    ["${REGISTRY}/backend.ai-appproxy-worker:${PKGVER}"],
    TAG_LATEST ? ["${REGISTRY}/backend.ai-appproxy-worker:latest"] : [],
  )
  cache-from = ["type=gha,scope=backend.ai-appproxy-worker"]
  cache-to   = ["type=gha,mode=max,scope=backend.ai-appproxy-worker"]
}
