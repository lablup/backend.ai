#!/bin/bash
set -e

# DooD (Docker-out-of-Docker) krunner path setup
#
# In DooD mode, the agent creates session containers via the host Docker daemon.
# When the agent bind-mounts krunner files (runner, kernel, helpers) into session
# containers, Docker resolves the source paths on the HOST filesystem, not inside
# the agent container. To make these paths accessible from the host, we:
# 1. Copy krunner packages to a shared volume path (/tmp/backend-ai-krunner/)
# 2. Replace the originals with symlinks so importlib.resources.files() resolves
#    to the shared path (via Path.resolve() in resolve_krunner_filepath)

KRUNNER_SHARED="/tmp/backend-ai-krunner"

if [ -d "$KRUNNER_SHARED" ]; then
    SITE_PKG=$(python3 -c "import site; print(site.getsitepackages()[0])")
    for pkg in runner kernel helpers; do
        src="$SITE_PKG/ai/backend/$pkg"
        dst="$KRUNNER_SHARED/$pkg"
        if [ -d "$src" ] && [ ! -L "$src" ]; then
            # First run: copy packages to shared volume and create symlinks
            cp -r "$src" "$dst"
            rm -rf "$src"
            ln -s "$dst" "$src"
        elif [ -L "$src" ]; then
            # Already symlinked (container restart)
            :
        fi
    done
fi

exec "$@"
