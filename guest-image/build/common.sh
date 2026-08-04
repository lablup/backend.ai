set -euo pipefail

BAI_CC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BAI_CC_OUT="${BAI_CC_OUT:-${BAI_CC_ROOT}/out}"
BAI_CC_CACHE="${BAI_CC_CACHE:-${BAI_CC_ROOT}/.cache}"
BAI_CC_KATA_SRC="${BAI_CC_KATA_SRC:-${BAI_CC_CACHE}/kata-src}"

set -a
. "${BAI_CC_ROOT}/pins.env"
set +a

log() { printf '[guest-image] %s\n' "$*" >&2; }
die() { printf '[guest-image] fatal: %s\n' "$*" >&2; exit 1; }

need() {
	for c in "$@"; do
		command -v "$c" >/dev/null 2>&1 || die "missing required command: $c"
	done
}

need_root() {
	[ "$(id -u)" -eq 0 ] || die "$1 must run as root"
}

sha256_of() { sha256sum "$1" | cut -d' ' -f1; }
sha384_of() { sha384sum "$1" | cut -d' ' -f1; }

fetch() {
	local url="$1" dest="$2" want="${3:-}"
	if [ ! -f "$dest" ]; then
		mkdir -p "$(dirname "$dest")"
		curl -fsSL --retry 3 -o "$dest.part" "$url"
		mv "$dest.part" "$dest"
	fi
	if [ -n "$want" ]; then
		local got
		got="$(sha256_of "$dest")"
		[ "$got" = "$want" ] || die "digest mismatch for $url: want $want got $got"
	fi
}

kata_variant_suffix() {
	case "${BAI_CC_BUILD_VARIANT}" in
		confidential) printf 'confidential' ;;
		nvidia-gpu-confidential) printf 'nvidia-gpu-confidential' ;;
		*) die "unsupported build variant: ${BAI_CC_BUILD_VARIANT}" ;;
	esac
}

canonicalise_tree() {
	local dir="$1"
	find "$dir" -exec touch -h -d "@${SOURCE_DATE_EPOCH}" {} +
}

canonical_tar() {
	local dir="$1" dest="$2"
	tar --sort=name --format=gnu --numeric-owner \
		--mtime="@${SOURCE_DATE_EPOCH}" \
		--pax-option=exthdr.name=%d/PaxHeaders/%f,delete=atime,delete=ctime \
		-C "$dir" -cf "$dest" .
}
