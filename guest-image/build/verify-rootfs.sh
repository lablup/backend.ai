#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

stage="${BAI_CC_OUT}/rootfs"
[ -d "$stage" ] || die "no staged rootfs; run build/rootfs.sh first"

fail=0
report() { printf '%-6s %s\n' "$1" "$2"; [ "$1" = "ok" ] || fail=1; }

for path in \
	sbin/mount.nfs sbin/mount.nfs4 sbin/mount.ceph sbin/cryptsetup \
	usr/bin/gocryptfs usr/bin/fusermount3 usr/bin/kata-agent \
	opt/backend.ai/bin/python opt/kernel/entrypoint.sh opt/kernel/bai-cc-entrypoint \
	opt/kernel/su-exec opt/kernel/dropbearmulti usr/local/bin/bai-guest-boot \
	usr/lib/systemd/system/bai-guest-boot.service \
	usr/bin/wg usr/sbin/ip usr/local/bin/bai-tunnel-up opt/kernel/bai-tunnel-bench \
	usr/lib/systemd/system/bai-tunnel-up.path usr/lib/systemd/system/bai-tunnel-up.service
do
	if [ -e "${stage}/${path}" ] || [ -e "${stage}/usr/${path}" ]; then
		report ok "$path"
	else
		report MISS "$path"
	fi
done

for gone in opt/kernel/libbaihook opt/kernel/jail; do
	compgen -G "${stage}/${gone}"'*' >/dev/null && report DROP "$gone must not be baked" || report ok "$gone absent"
done

config="$(find "${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build" -name '.config' -print -quit 2>/dev/null || true)"
if [ -n "$config" ]; then
	while IFS= read -r want; do
		case "$want" in
			''|'#'*) continue ;;
			*=n) ! grep -qE "^${want%%=*}=" "$config" ;;
			*) grep -qx "$want" "$config" ;;
		esac && report ok "kernel ${want%%=*}" || report MISS "kernel $want"
	done < "${BAI_CC_ROOT}/kernel/fragments/backendai.conf"
else
	report MISS "guest kernel .config not found for inspection"
fi

exit "$fail"
