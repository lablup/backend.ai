#!/usr/bin/env bash
# Builds every `main` package under `cmd/` for linux amd64 and arm64 into <out-dir>.
# VERSION and COMMIT are set into `main.version` and `main.commit`.
# Usage: VERSION=<tag> COMMIT=<sha> build-release.sh <out-dir>
set -euo pipefail

out="${1:?usage: build-release.sh <out-dir>}"
version="${VERSION:-dev}"
commit="${COMMIT:-$(git rev-parse HEAD)}"

packages="$(go list -f '{{if eq .Name "main"}}{{.ImportPath}}{{end}}' ./cmd/... | sed '/^$/d')"
if [ -z "$packages" ]; then
  echo "no main package under cmd/; nothing to build"
  exit 0
fi

mkdir -p "$out"
for pkg in $packages; do
  name="$(basename "$pkg")"
  for arch in amd64 arm64; do
    echo "build $name linux/$arch"
    CGO_ENABLED=0 GOOS=linux GOARCH="$arch" go build -trimpath \
      -ldflags "-s -w -X main.version=$version -X main.commit=$commit" \
      -o "$out/$name-linux-$arch" "$pkg"
  done
done
