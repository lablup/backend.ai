#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

stage="${BAI_CC_OUT}/rootfs"
[ -d "$stage" ] || die "no staged rootfs; run build/rootfs.sh first"

fail=0
report() { printf '%-6s %s\n' "$1" "$2"; [ "$1" = "ok" ] || fail=1; }

for path in \
	sbin/mount.nfs sbin/mount.nfs4 sbin/mount.ceph sbin/mount.cifs \
	sbin/cryptsetup sbin/mkfs.ext4 \
	usr/bin/gocryptfs usr/bin/fusermount3 usr/bin/kata-agent \
	opt/backend.ai/bin/python opt/kernel/entrypoint.sh opt/kernel/bai-cc-entrypoint \
	usr/bin/kata-agent.real opt/kernel/backendai.cdi.json \
	opt/kernel/su-exec opt/kernel/dropbearmulti usr/local/bin/bai-guest-boot \
	opt/kernel/bai-guest-storage usr/local/bin/bai-storage-fuse \
	usr/bin/wg usr/sbin/ip usr/local/bin/bai-tunnel-up opt/kernel/bai-tunnel-bench \
	usr/sbin/xtables-nft-multi usr/local/bin/bai-guest-egress \
	usr/lib/x86_64-linux-gnu/xtables/libxt_standard.so \
	usr/lib/x86_64-linux-gnu/xtables/libxt_tcp.so \
	usr/lib/x86_64-linux-gnu/xtables/libxt_udp.so \
	usr/lib/x86_64-linux-gnu/xtables/libxt_conntrack.so \
	etc/kata-opa/default-policy.rego
do
	if [ -e "${stage}/${path}" ] || [ -e "${stage}/usr/${path}" ]; then
		report ok "$path"
	else
		report MISS "$path"
	fi
done

for gone in opt/kernel/libbaihook opt/kernel/jail usr/lib/systemd usr/sbin/rpcbind \
	usr/sbin/rpc.statd usr/sbin/ntpd etc/kata-opa/allow-all.rego \
	usr/local/bin/bai-integrity-mount; do
	compgen -G "${stage}/${gone}"'*' >/dev/null \
		&& report DROP "$gone must not be baked" || report ok "$gone absent"
done

setuid="$(find "$stage" -type f -perm /6000 -printf '%P ' 2>/dev/null)"
[ -z "$setuid" ] && report ok "no setuid or setgid files" \
	|| report DROP "setuid or setgid present: $setuid"

magic="$(dd if="${stage}/usr/bin/kata-agent.real" bs=1 count=4 2>/dev/null | od -An -tx1 | tr -d ' \n')"
[ "$magic" = "7f454c46" ] && report ok "kata-agent.real is an ELF binary" \
	|| report MISS "kata-agent.real is not an ELF binary"

config="$(find "${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build/kernel-${BAI_CC_KERNEL_FLAVOUR}" \
	-name '.config' -print -quit 2>/dev/null || true)"
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
