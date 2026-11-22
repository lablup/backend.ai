#!/bin/sh
# Copy the kernel runner into DEST (an emptyDir shared with the session container), then
# place the kernel files listed in /kprep/manifest into /kconfig (/home/config) and /kwork (/home/work).
# Env: KRUNNER_LIBC (static-gnu|musllinux), KRUNNER_ARCH (x86_64|aarch64),
#      KRUNNER_LIBBAIHOOK (file name under runner/), KERNEL_UID, KERNEL_GID (the files' owner),
#      DEST (default /krunner-dest), KRUNNER_WAIT_PEERS (host names to wait for),
#      KRUNNER_WAIT_TIMEOUT (seconds, default 300).
set -eu
DEST=${DEST:-/krunner-dest}
LIBC=${KRUNNER_LIBC:-static-gnu}
ARCH=${KRUNNER_ARCH:-x86_64}
SRC=/krunner
RUNNER=$SRC/runner
KUID=${KERNEL_UID:-9001}
KGID=${KERNEL_GID:-9001}

fail() {
  echo "$*" >&2
  exit 1
}

# Each manifest line: <area> <secret key> <mode> <base64 of the path relative to the area>.
# Runs as the kernel user.
place_files() {
  umask 022
  # The Agent's home files first; the session's dotfiles in the manifest overwrite them.
  for f in .bashrc .bash_profile .zshrc .vimrc .tmux.conf DO_NOT_STORE_PERSISTENT_FILES_HERE.md; do
    cp "$RUNNER/$f" "/kwork/$f"
  done
  mkdir -p /kwork/.jupyter/custom
  cp "$RUNNER/jupyter-custom.css" /kwork/.jupyter/custom/custom.css
  cp "$RUNNER/logo.svg" "$RUNNER/roboto.ttf" "$RUNNER/roboto-italic.ttf" /kwork/.jupyter/custom/
  while read -r area key mode encoded rest; do
    [ -z "$rest" ] || fail "malformed manifest line"
    case "$area" in
      config) base=/kconfig ;;
      work) base=/kwork ;;
      *) fail "unknown kernel file area: $area" ;;
    esac
    case "$key" in
      f | f*[!0-9]*) fail "invalid kernel file key: $key" ;;
      f[0-9]*) ;;
      *) fail "invalid kernel file key: $key" ;;
    esac
    case "$mode" in
      [0-7][0-7][0-7] | 0[0-7][0-7][0-7]) ;;
      *) fail "invalid kernel file mode: $mode" ;;
    esac
    case "$encoded" in
      "" | *[!A-Za-z0-9+/=]*) fail "invalid kernel file path encoding" ;;
    esac
    path=$(printf '%s' "$encoded" | base64 -d) || fail "invalid kernel file path encoding"
    case "$path" in
      "" | /* | *[[:cntrl:]]*) fail "invalid kernel file path" ;;
    esac
    case "/$path/" in
      */../* | */./* | *//*) fail "invalid kernel file path" ;;
    esac
    src="/kprep/$key"
    [ -f "$src" ] || fail "kernel file $key is not a regular file"
    dest="$base/$path"
    mkdir -p "$(dirname "$dest")"
    parent=$(readlink -f "$(dirname "$dest")") || fail "unresolvable kernel file path"
    case "$parent/" in
      "$base"/*) ;;
      *) fail "kernel file path leaves $base" ;;
    esac
    if [ -L "$dest" ] || { [ -e "$dest" ] && [ ! -f "$dest" ]; }; then
      fail "kernel file destination is not a regular file"
    fi
    cp "$src" "$dest"
    chmod "$mode" "$dest"
  done < /kprep/manifest
  mkdir -p /kconfig/ssh
  "$RUNNER/dropbearmulti.$ARCH.bin" dropbearkey -t rsa -s 2048 -f /kconfig/ssh/dropbear_rsa_host_key >/dev/null
  chmod 0600 /kconfig/ssh/dropbear_rsa_host_key
  if [ -d /kwork/.ssh ]; then chmod 0700 /kwork/.ssh; fi
}

if [ "${1:-}" = place-files ]; then
  place_files
  exit 0
fi


rm -rf "$DEST/backend.ai" "$DEST/kernel" "$DEST/bin"
mkdir -p "$DEST/backend.ai" "$DEST/kernel" "$DEST/bin"
cp -a "$SRC/env/$LIBC/." "$DEST/backend.ai/"

copy() {  # copy <src under runner/> <dest> [optional]
  if [ -e "$RUNNER/$1" ]; then
    cp -r "$RUNNER/$1" "$2"
  elif [ "${3:-}" != "optional" ]; then
    echo "missing runner file: $1" >&2
    exit 1
  fi
}
copy "su-exec.$ARCH.bin" "$DEST/kernel/su-exec"
copy "${KRUNNER_LIBBAIHOOK:-libbaihook.ubuntu22.04.$ARCH.so}" "$DEST/kernel/libbaihook.so"
copy "dropbearmulti.$ARCH.bin" "$DEST/kernel/dropbearmulti"
copy "sftp-server.$ARCH.bin" "$DEST/kernel/sftp-server"
copy "tmux.$ARCH.bin" "$DEST/kernel/tmux"
copy "etty.$ARCH.bin" "$DEST/kernel/etty"
copy "ttyd_linux.$ARCH.bin" "$DEST/kernel/ttyd"
copy "bssh-server.$ARCH.bin" "$DEST/kernel/bssh-server" optional
copy yank.sh "$DEST/kernel/yank.sh"
copy entrypoint.sh "$DEST/kernel/entrypoint.sh"
copy extract_dotfiles.py "$DEST/kernel/extract_dotfiles.py"
copy fantompass.py "$DEST/kernel/fantompass.py"
copy hash_phrase.py "$DEST/kernel/hash_phrase.py"
copy words.json "$DEST/kernel/words.json"
copy terminfo.alpine3.8 "$DEST/kernel/terminfo" optional
copy "all-smi.$ARCH.bin" "$DEST/bin/all-smi"
copy "bssh.$ARCH.bin" "$DEST/bin/bssh"
chmod 0755 "$DEST"/kernel/* "$DEST"/bin/*  # terminfo is a directory, so 0755 suits it too
if [ -f /kprep/manifest ]; then
  # Only the two area roots change owner as root; the files are placed as the kernel user, so
  # a manifest entry cannot write where the kernel user cannot.
  chmod 0755 /kconfig /kwork  # an emptyDir is 0777; sshd refuses keys under a world-writable home
  chown "$KUID:$KGID" /kconfig /kwork
  "$RUNNER/su-exec.$ARCH.bin" "$KUID:$KGID" /bin/sh "$0" place-files
fi
echo "krunner installed: libc=$LIBC arch=$ARCH python=$(cat "$DEST/backend.ai/PYTHON_VERSION")"
# A session's Pods are bound together, but a peer's DNS record appears only with its IP; a
# lookup before that is a cached miss in the kernel, so the kernel starts after they resolve.
deadline=$(( $(date +%s) + ${KRUNNER_WAIT_TIMEOUT:-300} ))
for peer in ${KRUNNER_WAIT_PEERS:-}; do
  until nslookup "$peer" >/dev/null 2>&1; do
    if [ "$(date +%s)" -ge "$deadline" ]; then
      echo "peer $peer did not resolve" >&2
      exit 1
    fi
    sleep 1
  done
done
[ -n "${KRUNNER_WAIT_PEERS:-}" ] && echo "peers resolved: $KRUNNER_WAIT_PEERS"
exit 0
