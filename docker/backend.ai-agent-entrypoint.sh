#!/bin/bash
set -euo pipefail

# DooD (Docker-out-of-Docker) krunner path parity
#
# In DooD mode, the agent creates session containers via the host Docker daemon.
# When the agent bind-mounts krunner files into session containers — runner
# binaries/scripts, the kernel/helpers python packages, and the krunner-env
# archives (ai/backend/krunner/*) that prepare_krunner_env feeds to the
# krunner-extractor container — Docker resolves the source paths on the HOST
# filesystem, not inside the agent container. To make these paths accessible
# from the host, we:
# 1. Copy the krunner packages into a host-shared directory, namespaced by the
#    agent package version ($KRUNNER_SHARED/<version>/<pkg>). Each versioned
#    copy is published atomically (staged under a temporary name, then renamed)
#    and treated as immutable: when it already exists the copy is skipped, so
#    restarts are fast and two same-version agents cannot clobber each other,
#    while different versions never share a directory.
# 2. Replace the originals with symlinks so importlib.resources.files() resolves
#    to the shared path (via Path.resolve() in resolve_krunner_filepath and
#    prepare_krunner_env_impl).
#
# The shared path must be bind-mounted from the host at the SAME absolute path
# on both sides (see docker/README.md). When it is not, we fail fast here
# instead of letting kernel creation fail later with a cryptic
# 'bind source path does not exist' error. Set BACKENDAI_SKIP_KRUNNER_PARITY=1
# to skip this setup entirely (escape hatch for non-DooD experiments).

KRUNNER_SHARED="${BACKENDAI_KRUNNER_SHARED:-/var/lib/backend.ai/krunner}"

if [ "${BACKENDAI_SKIP_KRUNNER_PARITY:-}" = "1" ]; then
    echo "NOTICE: BACKENDAI_SKIP_KRUNNER_PARITY=1 is set; skipping the krunner path-parity setup." >&2
    echo "NOTICE: kernel creation in DooD mode WILL fail without it." >&2
else
    # Proceed when the share dir already exists, or when its parent is a
    # mountpoint — in the latter case the subdirectory we create below is
    # host-visible through the parity mount.
    if [ -d "$KRUNNER_SHARED" ] || mountpoint -q "$(dirname "$KRUNNER_SHARED")"; then
        mkdir -p "$KRUNNER_SHARED"
    else
        echo "FATAL: the krunner share $KRUNNER_SHARED is not available inside the container." >&2
        echo "FATAL: Bind-mount it (or its parent $(dirname "$KRUNNER_SHARED")) from the host at the" >&2
        echo "FATAL: SAME absolute path on both sides, e.g.:" >&2
        echo "FATAL:   -v $KRUNNER_SHARED:$KRUNNER_SHARED" >&2
        echo "FATAL: (see docker/README.md). To run without DooD kernel support," >&2
        echo "FATAL: set BACKENDAI_SKIP_KRUNNER_PARITY=1." >&2
        exit 1
    fi

    # Locate the site-packages root via the `site` module, NOT by resolving the
    # ai.backend.runner module path: on a container restart the package dirs
    # below are already symlinks into the share, so a resolve()d module path
    # would land inside the share instead of the real site-packages root.
    SITE_PKG=$(python3 -c "import site; print(site.getsitepackages()[0])")
    if [ ! -d "$SITE_PKG/ai/backend" ]; then
        # Fallback: locate the package as it appears on sys.path (deliberately
        # NOT resolve()d, for the same symlink reason as above).
        SITE_PKG=$(python3 -c "import ai.backend.runner, pathlib; print(pathlib.Path(ai.backend.runner.__file__).parent.parent.parent.parent)")
    fi

    PKGVER=$(python3 -c "import importlib.metadata; print(importlib.metadata.version('backend.ai-agent'))")
    mkdir -p "$KRUNNER_SHARED/$PKGVER"

    for pkg in runner kernel helpers krunner; do
        src="$SITE_PKG/ai/backend/$pkg"
        dst="$KRUNNER_SHARED/$PKGVER/$pkg"
        if [ -d "$src" ] && [ ! -L "$src" ]; then
            # Fresh container: publish this version's copy into the share
            # (unless a previous same-version agent already did), then replace
            # the package with a symlink.
            if [ ! -e "$dst" ]; then
                # Atomic publish: stage under a temporary name and rename into
                # place so a crash or a concurrent agent never exposes a
                # half-written copy.
                rm -rf "$dst.new"
                cp -a "$src" "$dst.new"
                rm -rf "$dst"
                mv "$dst.new" "$dst"
            fi
            rm -rf "$src"
            ln -s "$dst" "$src"
        elif [ -L "$src" ]; then
            # Container restart: the symlink is already in place; just make
            # sure it is not dangling (e.g. the share was wiped or remounted
            # empty between runs).
            if [ ! -e "$src" ]; then
                if [ -e "$dst" ]; then
                    ln -sfn "$dst" "$src"
                else
                    echo "FATAL: $src is a dangling symlink and $dst does not exist." >&2
                    echo "FATAL: The krunner share no longer holds this version's copy;" >&2
                    echo "FATAL: recreate the container to repopulate it." >&2
                    exit 1
                fi
            fi
        else
            echo "FATAL: $src not found (neither a directory nor a symlink); the image is broken." >&2
            exit 1
        fi
    done
fi

# These dirs also exist in the image, but volume/tmpfs mounts over their parents
# can shadow them; recreate so non-parity setups keep working too.
mkdir -p /var/log/backend.ai
mkdir -p /tmp/backend.ai/ipc

exec "$@"
