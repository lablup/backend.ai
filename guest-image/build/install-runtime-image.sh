#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need install sed grep

need_root "install-runtime-image.sh"

config="${BAI_CC_KATA_CONFIG:-/opt/kata/share/defaults/kata-containers/configuration-backendai-cc.toml}"
[ -r "$config" ] || die "$config is not readable; the runtime class must exist before an image is installed"

image_src="${BAI_CC_OUT}/kata-containers-backendai.img"
kernel_src="${BAI_CC_OUT}/vmlinuz.container"
params_src="${BAI_CC_OUT}/kernel_verity_params.txt"
for f in "$image_src" "$kernel_src" "$params_src"; do
	[ -s "$f" ] || die "$f is missing; run 'make manifest' first"
done

setting_of() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$config" | head -1; }

image_dst="$(setting_of image)"
kernel_dst="$(setting_of kernel)"
[ -n "$image_dst" ] || die "$config names no image"
[ -n "$kernel_dst" ] || die "$config names no kernel"
grep -q '^[[:space:]]*kernel_verity_params[[:space:]]*=' "$config" \
	|| die "$config carries no kernel_verity_params line to update; refusing to guess where it belongs"

params="$(tr -d '[:space:]' < "$params_src")"
install -m 0644 "$image_src" "$image_dst"
install -m 0644 "$kernel_src" "$kernel_dst"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
awk -v params="$params" '
	/^[[:space:]]*kernel_verity_params[[:space:]]*=/ { printf "kernel_verity_params = \"%s\"\n", params; next }
	{ print }
' "$config" > "$tmp"
install -m 0644 "$tmp" "$config"

readback="$(setting_of kernel_verity_params)"
[ "$readback" = "$params" ] || die "kernel_verity_params reads back as $readback, not $params"
cmp -s "$image_src" "$image_dst" || die "$image_dst does not match $image_src"
cmp -s "$kernel_src" "$kernel_dst" || die "$kernel_dst does not match $kernel_src"

log "installed $(basename "$image_dst") $(sha256_of "$image_dst")"
log "installed $(basename "$kernel_dst") $(sha256_of "$kernel_dst")"
log "kernel_verity_params $params"
