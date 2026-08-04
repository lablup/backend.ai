#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need python3
need_root "reproduce.sh"

reference="${1:-${BAI_CC_OUT}/build-manifest.json}"
[ -f "$reference" ] || die "no reference manifest at $reference"
keep="$(mktemp)"
cp "$reference" "$keep"

BAI_CC_OUT="${BAI_CC_OUT}" "${BAI_CC_ROOT}/build/rootfs.sh"
BAI_CC_OUT="${BAI_CC_OUT}" "${BAI_CC_ROOT}/build/image.sh"

python3 - "$keep" "${BAI_CC_OUT}/rootfs.tar" "${BAI_CC_OUT}/kata-containers-backendai.img" \
	"${BAI_CC_OUT}/kernel_verity_params.txt" <<'PY'
import hashlib, json, pathlib, sys

ref = json.loads(pathlib.Path(sys.argv[1]).read_text())
def digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

checks = [
    ("rootfs_tar_sha256", ref["artifacts"]["rootfs_tar_sha256"], digest(sys.argv[2])),
    ("image_sha256", ref["artifacts"]["image_sha256"], digest(sys.argv[3])),
    ("kernel_verity_params", ref["measurement"]["kernel_verity_params"],
     pathlib.Path(sys.argv[4]).read_text().strip()),
]
bad = [(n, w, g) for n, w, g in checks if w != g]
for name, want, got in checks:
    print(f"{'OK  ' if want == got else 'DIFF'} {name}\n  registered {want}\n  rebuilt    {got}")
sys.exit(1 if bad else 0)
PY
