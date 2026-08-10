#!/bin/bash
set -e

# DooD (Docker-out-of-Docker) krunner path setup
#
# In DooD mode, the agent creates session containers via the host Docker daemon.
# When the agent bind-mounts krunner files into session containers — runner
# binaries/scripts, the kernel/helpers python packages, and the krunner-env
# archives (ai/backend/krunner/*) that prepare_krunner_env feeds to the
# krunner-extractor container — Docker resolves the source paths on the HOST
# filesystem, not inside the agent container. To make these paths accessible
# from the host, we:
# 1. Copy krunner packages to a shared volume path (/tmp/backend-ai-krunner/)
# 2. Replace the originals with symlinks so importlib.resources.files() resolves
#    to the shared path (via Path.resolve() in resolve_krunner_filepath and
#    prepare_krunner_env_impl)
#
# The shared path must be bind-mounted from the host at the SAME absolute path
# on both sides; when it is not mounted, the setup is skipped (non-DooD usage).

KRUNNER_SHARED="/tmp/backend-ai-krunner"

if [ ! -d "$KRUNNER_SHARED" ]; then
    echo "WARNING: $KRUNNER_SHARED is not mounted; skipping the krunner path-parity setup." >&2
    echo "WARNING: kernel creation WILL fail with 'bind source path does not exist' unless" >&2
    echo "WARNING: $KRUNNER_SHARED is bind-mounted from the host at the same path (see docker/README.md)." >&2
fi

if [ -d "$KRUNNER_SHARED" ]; then
    SITE_PKG=$(python3 -c "import site; print(site.getsitepackages()[0])")
    for pkg in runner kernel helpers krunner; do
        src="$SITE_PKG/ai/backend/$pkg"
        dst="$KRUNNER_SHARED/$pkg"
        if [ -d "$src" ] && [ ! -L "$src" ]; then
            # Fresh container: refresh the shared copy and replace the package
            # with a symlink. Remove any copy left by a previous container
            # first — `cp -r` into an existing directory would nest instead of
            # replace, leaving stale content behind after an image upgrade.
            rm -rf "$dst"
            cp -r "$src" "$dst"
            rm -rf "$src"
            ln -s "$dst" "$src"
        elif [ -L "$src" ]; then
            # Already symlinked (container restart)
            :
        fi
    done
fi

# Log directory creation
mkdir -p /var/log/backend.ai

# IPC directory creation
mkdir -p /tmp/backend.ai/ipc

exec "$@"
