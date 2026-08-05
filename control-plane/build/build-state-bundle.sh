#!/bin/bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TREE=$(cd "${HERE}/.." && pwd)
REPO=$(cd "${TREE}/.." && pwd)

set -a
. "${HERE}/pins.env"
set +a
MIRROR="${MIRROR_BASE}/${SNAPSHOT}"
ETCD_URL="https://github.com/etcd-io/etcd/releases/download/${ETCD_VERSION}/etcd-${ETCD_VERSION}-linux-amd64.tar.gz"
VALKEY_URL="https://download.valkey.io/releases/valkey-${VALKEY_VERSION}-noble-x86_64.tar.gz"

PACKAGES=(systemd systemd-sysv systemd-boot dracut dracut-network isc-dhcp-client
          linux-image-virtual "linux-modules-extra-${KERNEL_ABI}" cryptsetup-bin erofs-utils openssl python3
          postgresql-16 postgresql-client-16 ca-certificates iproute2 curl)

OUT=${1:?usage: build-state-bundle.sh <output-dir> <manager> <coordinator> <kbs-client> [kernel]}
MANAGER_PEX=${2:?manager pex}
COORDINATOR_PEX=${3:?coordinator pex}
KBS_CLIENT=${4:?kbs-client binary}
KERNEL=${5:-}
ROOT="${OUT}/rootfs"

fail() { echo "build-state-bundle: $*" >&2; exit 1; }

for pin in ETCD_SHA256 VALKEY_SHA256 SUITE MIRROR_BASE SNAPSHOT SOURCE_DATE_EPOCH IMAGE_UUID KERNEL_ABI \
           COMMITTED_RPC_KEY_SHA256 BACKENDAI_KBS_URL; do
    value=${!pin:-}
    [ -n "$value" ] || fail "${pin} is unset"
    [ "$value" != "PIN-ME" ] || fail "${pin} is unpinned; fill it from the release you intend to ship"
done

verify() {
    local want=$1 path=$2
    local got
    got=$(sha256sum "$path" | cut -d' ' -f1)
    [ "$got" = "$want" ] || fail "$path digest $got does not match the pinned $want"
}

fetch() {
    curl -fsSL --retry 3 -o "$2" "$1"
    verify "$3" "$2"
}

if [ -n "${BAI_REUSE_ROOTFS:-}" ] && [ -x "$ROOT/usr/bin/dracut" ]; then
    echo "build-state-bundle: reusing the root filesystem already under ${ROOT}" >&2
else
    rm -rf "$OUT"
    mkdir -p "$ROOT"
    debootstrap --variant=minbase --merged-usr --components=main,universe \
        --include="$(IFS=,; echo "${PACKAGES[*]}")" "$SUITE" "$ROOT" "$MIRROR"
fi
mkdir -p "$OUT/cache"

unbind() {
    for point in dev/pts dev sys proc; do
        mountpoint -q "${ROOT}/${point}" && umount -l "${ROOT}/${point}"
    done
    return 0
}
bind() {
    mount --bind /proc "${ROOT}/proc"
    mount --bind /sys "${ROOT}/sys"
    mount --bind /dev "${ROOT}/dev"
    mount --bind /dev/pts "${ROOT}/dev/pts"
}
trap unbind EXIT

fetch "$ETCD_URL" "$OUT/cache/etcd.tgz" "$ETCD_SHA256"
tar -xzf "$OUT/cache/etcd.tgz" -C "$OUT/cache"
install -m 0755 "$OUT"/cache/etcd-*/etcd "$OUT"/cache/etcd-*/etcdctl "$OUT"/cache/etcd-*/etcdutl "$ROOT/usr/bin/"

fetch "$VALKEY_URL" "$OUT/cache/valkey.tgz" "$VALKEY_SHA256"
tar -xzf "$OUT/cache/valkey.tgz" -C "$OUT/cache"
install -m 0755 "$OUT"/cache/valkey-*/bin/valkey-server "$OUT"/cache/valkey-*/bin/valkey-cli "$ROOT/usr/bin/"

install -d -m 0755 "$ROOT/usr/lib/backendai" "$ROOT/etc/backendai" \
    "$ROOT/usr/share/backendai/credential-templates" \
    "$ROOT/usr/lib/backendai/credential-broker" \
    "$ROOT/usr/lib/dracut/modules.d/91backendai-unlock"
install -m 0755 "$MANAGER_PEX" "$ROOT/usr/lib/backendai/backendai-manager"
install -m 0755 "$COORDINATOR_PEX" "$ROOT/usr/lib/backendai/backendai-appproxy-coordinator"
install -m 0755 "$KBS_CLIENT" "$ROOT/usr/bin/kbs-client"
cp -a "${REPO}/credential-broker/broker" "$ROOT/usr/lib/backendai/credential-broker/"
find "$ROOT/usr/lib/backendai/credential-broker" -name __pycache__ -type d -prune -exec rm -rf {} +
install -m 0644 "${REPO}"/credential-broker/templates/* "$ROOT/usr/share/backendai/credential-templates/"
sed "s|^url = .*|url = \"${BACKENDAI_KBS_URL}\"|" \
    "${REPO}/credential-broker/policy/state-bundle.toml" > "$ROOT/etc/backendai/credential-policy.toml"
chmod 0644 "$ROOT/etc/backendai/credential-policy.toml"
install -m 0755 "${TREE}"/bin/* "$ROOT/usr/lib/backendai/"
rm -f "$ROOT"/usr/lib/systemd/system/backendai-*.service \
      "$ROOT"/usr/lib/systemd/system/backendai-*.timer \
      "$ROOT"/etc/systemd/system/*.wants/backendai-*
install -m 0644 "${TREE}"/units/*.service "${TREE}"/units/*.timer "${TREE}"/units/*.mount \
    "$ROOT/usr/lib/systemd/system/"
install -m 0644 "${TREE}/units/backendai-state.conf" "$ROOT/usr/lib/tmpfiles.d/"
install -m 0755 "${TREE}/initramfs/module-setup.sh" "$ROOT/usr/lib/dracut/modules.d/91backendai-unlock/"
install -m 0755 "${TREE}/initramfs/unlock-state-volume" "$ROOT/usr/lib/dracut/modules.d/91backendai-unlock/"
install -m 0644 "${TREE}/initramfs/backendai-unlock-state.service" "$ROOT/usr/lib/dracut/modules.d/91backendai-unlock/"

rm -rf "$ROOT/usr/lib/backendai/no-introspection-aiomonitor"
cp -a "${HERE}/no-introspection/aiomonitor" "$ROOT/usr/lib/backendai/no-introspection-aiomonitor"

bind
chroot "$ROOT" /bin/sh -e <<'INSIDE'
id -u backendai >/dev/null 2>&1 || useradd --system --home-dir /var/lib/backendai --create-home backendai
id -u etcd >/dev/null 2>&1 || useradd --system --home-dir /var/lib/backendai/etcd --create-home etcd
id -u valkey >/dev/null 2>&1 || useradd --system --home-dir /var/lib/backendai/valkey --create-home valkey
install -d -m 0700 -o postgres -g postgres /var/lib/backendai/postgresql
install -d -m 0750 -o backendai -g backendai /var/lib/backendai/manager /var/lib/backendai/coordinator
systemctl enable var-log.mount var-lib-backendai.mount \
    backendai-credentials.service backendai-postgresql.service \
    backendai-postgresql-bootstrap.service backendai-etcd.service \
    backendai-etcd-bootstrap.service backendai-valkey.service \
    backendai-manager-schema.service backendai-etcdprobe.service backendai-manager.service \
    backendai-manager-selfcheck.service \
    backendai-appproxy-coordinator.service backendai-state-backup.timer
: > /etc/machine-id
systemctl mask systemd-timesyncd.service serial-getty@ttyS0.service getty@.service \
    debug-shell.service systemd-ask-password-console.service \
    postgresql.service postgresql@.service motd-news.timer
apt-get -y purge openssh-server 2>/dev/null || true
apt-get -y clean
rm -rf /var/lib/apt/lists/* /var/cache/debconf/*-old /usr/share/doc /usr/share/man
rm -rf /var/log/* /var/cache/ldconfig/* /var/lib/systemd/catalog/database
rm -f /var/lib/dpkg/status-old /var/lib/dpkg/available-old /etc/passwd- /etc/group- /etc/shadow- /etc/gshadow- /etc/subuid- /etc/subgid-
INSIDE
unbind

for pex in backendai-manager backendai-appproxy-coordinator; do
    find "$ROOT/usr/lib/backendai" -path "*/${pex}*" -name 'aiomonitor' -type d -prune -exec rm -rf {} + 2>/dev/null || true
done
python3 - "$ROOT" <<'PY'
import pathlib, shutil, sys
root = pathlib.Path(sys.argv[1])
shim = root / "usr/lib/backendai/no-introspection-aiomonitor"
removed = 0
for target in root.rglob("aiomonitor"):
    if target.is_dir() and target != shim and "no-introspection" not in str(target):
        shutil.rmtree(target)
        shutil.copytree(shim, target)
        removed += 1
for target in root.rglob("aiomonitor*.dist-info"):
    shutil.rmtree(target, ignore_errors=True)
print(f"build-state-bundle: replaced {removed} aiomonitor trees with the absent shim")
PY

SCRUBBED=true
for binary in "$ROOT/usr/lib/backendai/backendai-manager" \
              "$ROOT/usr/lib/backendai/backendai-appproxy-coordinator"; do
    head -c 4 "$binary" | grep -qa ELF && SCRUBBED=false
done
if [ "$SCRUBBED" = true ]; then
    if grep -rql "aiomonitor.termui\|start_monitor(" "$ROOT/usr/lib/backendai" 2>/dev/null; then
        fail "an introspection console implementation survived in the image"
    fi
else
    grep -q '^aiomonitor-enabled = false' \
        "$ROOT/usr/share/backendai/credential-templates/manager.toml.in" ||
        fail "the measured manager configuration does not disable the introspection console"
    if ! python3 - "$ROOT/usr/lib/backendai/backendai-manager" <<'CHECK'
import sys, zipfile
try:
    archive = zipfile.ZipFile(sys.argv[1])
    named = [n for n in archive.namelist() if n.endswith("manager/config/unified.py")]
    carries = bool(named) and b"aiomonitor-enabled" in archive.read(named[0])
except Exception:
    carries = False
sys.exit(0 if carries else 1)
CHECK
    then
        fail "the manager artifact predates the introspection-console switch, so setting it in the configuration would be silently ignored; rebuild the manager from a tree that carries manager.aiomonitor-enabled"
    fi
    echo "build-state-bundle: the introspection console survives inside an interpreter binary; the measured configuration switches it off and the artifact honours that switch" >&2
fi
if [ -e "$ROOT/usr/sbin/sshd" ] || [ -e "$ROOT/usr/bin/sshd" ]; then
    fail "a secure shell daemon survived in the image"
fi
if find "$ROOT" -type f -size -8k -exec sha256sum {} + | grep -q "$COMMITTED_RPC_KEY_SHA256"; then
    fail "the repository-committed default RPC private key survived in the image"
fi
grep -q '0.0.0+absent' "$ROOT/usr/lib/backendai/no-introspection-aiomonitor/__init__.py" ||
    fail "the introspection shim is missing"

[ -n "$KERNEL" ] || KERNEL=$(ls "$ROOT"/boot/vmlinuz-* | sort | tail -n 1)
KVER=$(basename "$KERNEL" | sed 's/^vmlinuz-//')
bind
chroot "$ROOT" dracut --force --no-hostonly --add "backendai-unlock systemd-veritysetup" \
    --add-drivers "erofs dm-verity dm-crypt tdx_guest tsm virtio_blk virtio_net virtio_pci" \
    --kver "$KVER" /boot/initrd.img
cp "$ROOT/boot/initrd.img" "$OUT/initrd.img"
cp "$KERNEL" "$OUT/vmlinuz"
rm -f "$ROOT/boot/initrd.img"

unbind
trap - EXIT

find "$ROOT" -newermt "@${SOURCE_DATE_EPOCH}" -print0 |
    xargs -0r touch --no-dereference --date="@${SOURCE_DATE_EPOCH}"
mkfs.erofs -zlz4hc -T "$SOURCE_DATE_EPOCH" -U "$IMAGE_UUID" --all-root "$OUT/rootfs.erofs" "$ROOT"

veritysetup format "$OUT/rootfs.erofs" "$OUT/rootfs.verity" --uuid "$IMAGE_UUID" |
    tee "$OUT/verity.txt"
ROOTHASH=$(awk '/Root hash:/ { print $3 }' "$OUT/verity.txt")
[ -n "$ROOTHASH" ] || fail "veritysetup produced no root hash"

CMDLINE="root=/dev/mapper/root ro systemd.verity=yes roothash=${ROOTHASH} \
BACKENDAI_KBS_URL=${BACKENDAI_KBS_URL:?BACKENDAI_KBS_URL must be set for the measured command line} \
BACKENDAI_STATE_DEVICE=/dev/disk/by-partlabel/backendai-state rd.neednet=1 ip=dhcp console=ttyS0"
printf '%s' "$CMDLINE" > "$OUT/cmdline"
ukify build --linux="$KERNEL" --initrd="$OUT/initrd.img" --cmdline="@${OUT}/cmdline" \
    --os-release="@${ROOT}/usr/lib/os-release" --output="$OUT/state-bundle.efi"

python3 - "$OUT" "$ROOTHASH" "$IMAGE_UUID" "$SCRUBBED" > "$OUT/reference-values.json" <<'PY'
import hashlib, json, pathlib, sys
out, roothash, uuid = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
scrubbed = sys.argv[4] == "true"


def digest(name, algorithm):
    h = hashlib.new(algorithm)
    h.update((out / name).read_bytes())
    return h.hexdigest()


json.dump(
    {
        "version": "0.1.0",
        "bundle": "state",
        "image-uuid": uuid,
        "verity-root-hash": roothash,
        "uki-sha384": digest("state-bundle.efi", "sha384"),
        "cmdline-sha384": digest("cmdline", "sha384"),
        "rootfs-sha256": digest("rootfs.erofs", "sha256"),
        "introspection-scrubbed": scrubbed,
        "rtmr": "capture-reference-values must fill these from a booted trust domain",
    },
    sys.stdout,
    indent=2,
    sort_keys=True,
)
PY

echo "build-state-bundle: ${OUT}/state-bundle.efi roothash=${ROOTHASH}"
