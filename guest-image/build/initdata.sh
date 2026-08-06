#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need gzip base64 sha384sum

kbs_url="${BAI_CC_KBS_URL:-}"
[ -n "$kbs_url" ] || die "BAI_CC_KBS_URL must name the authorisation shim; there is no safe default"
ca_file="${BAI_CC_REGISTRY_CA:-}"
[ -r "$ca_file" ] || die "BAI_CC_REGISTRY_CA must point at the registry certificate authority the guest pulls against"
registry_ca="$(cat "$ca_file")"

blobs="${BAI_CC_OUT}/initdata"
mkdir -p "$blobs"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

toml_array() {
	local item out=""
	for item in $1; do
		out="${out:+${out}, }\"${item}\""
	done
	printf '%s' "$out"
}

render() {
	sed -e "s|@KBS_URL@|${kbs_url}|g" \
		-e "s|@EGRESS_RESOLVERS@|$(toml_array "${BAI_CC_EGRESS_RESOLVERS}")|g" \
		-e "s|@EGRESS_HOSTS@|$(toml_array "${BAI_CC_EGRESS_HOSTS}")|g" \
		-e "s|@TIME_RESOURCE@|${BAI_CC_TIME_RESOURCE}|g" \
		-e "s|@TIME_SKEW_BOUND@|${BAI_CC_TIME_SKEW_BOUND}|g" \
		-e "s|@TIME_REANCHOR_INTERVAL@|${BAI_CC_TIME_REANCHOR_INTERVAL}|g" \
		-e "s|@ALLOW_SUDO@|${BAI_CC_ALLOW_SUDO}|g" \
		-e "s|@GPU_VBIOS@|${BAI_CC_GPU_VBIOS}|g" \
		-e "s|@GPU_DRIVER@|${BAI_CC_GPU_DRIVER}|g" "$1" \
		| awk -v ca="$registry_ca" '{ gsub(/@REGISTRY_CA@/, ca); print }'
}

emit_key() {
	local name="$1" src="$2"
	! grep -q "'''" "$src" || die "$src contains a TOML literal-string terminator"
	printf '\n"%s" = %s\n' "$name" "'''" >> "${tmp}/initdata.toml"
	render "$src" >> "${tmp}/initdata.toml"
	printf "%s\n" "'''" >> "${tmp}/initdata.toml"
}

{
	printf 'version = "0.1.0"\n'
	printf 'algorithm = "%s"\n' "${BAI_CC_INITDATA_ALGORITHM}"
	printf '\n[data]\n'
} > "${tmp}/initdata.toml"

emit_key "cdh.toml" "${BAI_CC_ROOT}/config/cdh.toml"
emit_key "aa.toml" "${BAI_CC_ROOT}/config/aa.toml"
emit_key "policy.rego" "${BAI_CC_ROOT}/policy/agent-policy.rego"
emit_key "backendai.toml" "${BAI_CC_ROOT}/config/backendai.toml"
case "${BAI_CC_BUILD_VARIANT}" in
	*nvidia-gpu*) emit_key "gpu-policy.json" "${BAI_CC_ROOT}/config/gpu-policy.json" ;;
esac
for extra in "$@"; do
	emit_key "$(basename "$extra")" "$extra"
done

digest="$(sha384_of "${tmp}/initdata.toml")"
target="${blobs}/${digest}.toml"
if [ -f "$target" ]; then
	cmp -s "$target" "${tmp}/initdata.toml" || die "content-addressed blob ${digest} differs from its own digest"
	log "blob ${digest} already published; not re-rendered"
else
	install -m 0444 "${tmp}/initdata.toml" "$target"
	gzip -n -c "$target" | base64 -w0 > "${blobs}/${digest}.b64"
	chmod 0444 "${blobs}/${digest}.b64"
fi

printf '%s\n' "$digest" > "${BAI_CC_OUT}/mr_config_id.txt"
log "mr_config_id ${digest}"
log "annotation io.katacontainers.config.hypervisor.cc_init_data=@${blobs}/${digest}.b64"
