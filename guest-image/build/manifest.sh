#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need openssl python3

image="${BAI_CC_OUT}/kata-containers-backendai.img"
[ -f "$image" ] || die "no image; run build/image.sh first"
[ -n "${BAI_CC_SIGNING_KEY:-}" ] || die "BAI_CC_SIGNING_KEY must point at the build pipeline signing key"

manifest="${BAI_CC_OUT}/build-manifest.json"

BAI_CC_IMAGE_SHA256="$(sha256_of "$image")" \
BAI_CC_ROOTFS_SHA256="$(sha256_of "${BAI_CC_OUT}/rootfs.tar")" \
BAI_CC_KERNEL_SHA256="$(sha256_of "${BAI_CC_OUT}/vmlinuz.container")" \
BAI_CC_VERITY_PARAMS="$(cat "${BAI_CC_OUT}/kernel_verity_params.txt")" \
BAI_CC_KATA_SRC="${BAI_CC_KATA_SRC}" \
BAI_CC_OUT="${BAI_CC_OUT}" \
python3 - "$manifest" <<'PY'
import hashlib, json, os, pathlib, sys

out = pathlib.Path(os.environ["BAI_CC_OUT"])
pins = {k: v for k, v in os.environ.items() if k.startswith("BAI_CC_")}
for drop in ("BAI_CC_OUT", "BAI_CC_CACHE", "BAI_CC_KATA_SRC", "BAI_CC_SIGNING_KEY", "BAI_CC_ROOT",
             "BAI_CC_IMAGE_SHA256", "BAI_CC_ROOTFS_SHA256", "BAI_CC_KERNEL_SHA256", "BAI_CC_VERITY_PARAMS"):
    pins.pop(drop, None)

blobs = {}
for path in sorted((out / "initdata").glob("*.toml")):
    raw = path.read_bytes()
    blobs[path.stem] = {
        "bytes": len(raw),
        "sha384": hashlib.sha384(raw).hexdigest(),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    assert blobs[path.stem]["sha384"] == path.stem, path

manifest = {
    "schema": "backend.ai/confidential-guest-image/1",
    "pins": dict(sorted(pins.items())),
    "artifacts": {
        "image_sha256": os.environ["BAI_CC_IMAGE_SHA256"],
        "rootfs_tar_sha256": os.environ["BAI_CC_ROOTFS_SHA256"],
        "kernel_sha256": os.environ["BAI_CC_KERNEL_SHA256"],
    },
    "measurement": {
        "kernel_verity_params": os.environ["BAI_CC_VERITY_PARAMS"],
        "mr_config_id": sorted(blobs),
    },
    "initdata": blobs,
}
pathlib.Path(sys.argv[1]).write_bytes(
    json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
)
PY

openssl pkeyutl -sign -rawin -inkey "${BAI_CC_SIGNING_KEY}" \
	-in "$manifest" -out "${manifest}.sig"
openssl pkey -in "${BAI_CC_SIGNING_KEY}" -pubout -out "${manifest}.pub"
openssl pkeyutl -verify -rawin -pubin -inkey "${manifest}.pub" \
	-in "$manifest" -sigfile "${manifest}.sig" >/dev/null \
	|| die "manifest signature does not verify against its own key"

log "manifest $(sha256_of "$manifest") signed"
