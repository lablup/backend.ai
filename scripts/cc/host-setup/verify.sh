#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"

COCO_MODE=/home/devops/coco/tools/coco-mode
BROKER_URL="${BROKER_URL:-http://127.0.0.1:8080}"
MODELS_IMG="${MODELS_IMG:-/data/models.img}"
FAILED=0
SKIPPED=0

expect() {
    local what=$1 want=$2 got
    shift 2
    got=$("$@" 2>/dev/null | tr -d '\n')
    if [[ $got == $want ]]; then
        ok "$what — $got"
    else
        bad "$what — wanted '$want', saw '${got:-nothing}'"
        FAILED=$((FAILED + 1))
    fi
}

present() {
    local what=$1
    shift
    if "$@" >/dev/null 2>&1; then ok "$what"; else bad "$what"; FAILED=$((FAILED + 1)); fi
}

privileged() {
    local what=$1
    shift
    if [[ $(id -u) -ne 0 ]]; then
        warn "$what — needs root, skipped"
        SKIPPED=$((SKIPPED + 1))
    else
        present "$what" "$@"
    fi
}

absent() {
    local what=$1
    shift
    if "$@" >/dev/null 2>&1; then bad "$what"; FAILED=$((FAILED + 1)); else ok "$what"; fi
}

kernel_says() { journalctl -k -b | grep -q "$1"; }
grep_file() { [[ -r $1 ]] && grep -q "$2" "$1"; }
lsmod_has() { lsmod | grep -q "$1"; }
quoting_socket() { ss -l --vsock | grep -q ':4050'; }
caching_service_answers() { [[ $(curl -ks -o /dev/null -w '%{http_code}' https://localhost:8081/sgx/certification/v4/rootcacrl) == 200 ]]; }
caching_service_keyless() { ! grep -q 'Ocp-Apim-Subscription-Key' /opt/intel/sgx-dcap-pccs/pcs_client/pcs_client.js; }
kata_version() { /opt/kata/bin/kata-runtime --version | head -1; }
models_attached() { [[ ! -e $MODELS_IMG ]] || losetup -j "$MODELS_IMG" | grep -q .; }
accelerator_ready() {
    local status bound total on queried
    status=$("$COCO_MODE" status 2>/dev/null) || return 1
    bound=$(grep -c 'driver=vfio-pci' <<<"$status")
    total=$(grep -c 'driver=' <<<"$status")
    on=$(grep -c 'CC mode is on' <<<"$status")
    queried=$(grep -c 'CC mode is ' <<<"$status")
    (( total > 0 && bound == total && queried > 0 && on == queried ))
}
broker_probe() { curl -s -o /dev/null -w '%{http_code}' "$BROKER_URL/kbs/v0/resource/default/probe/probe"; }

info "read-only inspection of $(hostname); nothing below changes anything"

info "firmware and host trusted-domain support"
present "memory encryption enabled in firmware" kernel_says 'x86/tme: enabled by BIOS'
present "trusted-domain extensions enabled in firmware" kernel_says 'virt/tdx: BIOS enabled'
present "secure-arbitration module initialised" kernel_says 'virt/tdx: module initialized'
absent "no module call failed this boot" kernel_says 'SEAMCALL.*failed'
expect "virtualisation driver armed" Y cat /sys/module/kvm_intel/parameters/tdx
present "hibernation disabled on the command line" grep -qw nohibernate /proc/cmdline
present "guard-extension provisioning node" test -e /dev/sgx_provision
present "memory expander not onlined as system memory" grep_file /etc/modprobe.d/blacklist-kmem.conf 'blacklist kmem'
present "host virtual-network module loaded" lsmod_has vhost_net

info "quoting and collateral"
present "quote generation service active" systemctl is-active --quiet qgsd
present "quote generation service listening on the virtual socket" quoting_socket
present "caching service answering" caching_service_answers
present "caching service still running keyless" caching_service_keyless
privileged "platform registration already fired" grep -q 'passed successfully' /var/log/mpa_registration.log
present "collateral configuration points at the local caching service" grep_file /etc/sgx_default_qcnl.conf 8081

info "runtime"
expect "kata runtime" "*3.31.0*" kata_version
present "confidential runtime configuration present" test -e /opt/kata/share/defaults/kata-containers/configuration-qemu-tdx.toml
present "accelerator runtime configuration present" test -e /opt/kata/share/defaults/kata-containers/configuration-qemu-nvidia-gpu-tdx.toml
present "guest pull forced on the confidential class" grep_file /opt/kata/share/defaults/kata-containers/configuration-qemu-tdx.toml '^experimental_force_guest_pull = true'
present "guest pull forced on the accelerator class" grep_file /opt/kata/share/defaults/kata-containers/configuration-qemu-nvidia-gpu-tdx.toml '^experimental_force_guest_pull = true'
present "orchestrator cold-plug path disabled" grep_file /opt/kata/share/defaults/kata-containers/configuration-qemu-nvidia-gpu-tdx.toml '^pod_resource_api_sock = ""'
present "confidential shim wrapper installed" grep_file /usr/local/bin/containerd-shim-kata-qemu-tdx-v2 'configuration-qemu-tdx.toml'
present "accelerator shim wrapper installed" grep_file /usr/local/bin/containerd-shim-kata-qemu-nvidia-gpu-tdx-v2 'configuration-qemu-nvidia-gpu-tdx.toml'
present "container runtime active" systemctl is-active --quiet containerd
present "bridge plugin installed" test -e /opt/cni/bin/bridge

info "image supply"
expect "image registry" running nerdctl inspect registry --format '{{.State.Status}}'
expect "image registry restarts on boot" always nerdctl inspect registry --format '{{.HostConfig.RestartPolicy.Name}}'
present "model image attached as a loop device" models_attached

info "accelerators"
present "accelerator mode script reachable at its full path" test -x "$COCO_MODE"
present "every accelerator bound to the passthrough driver and in confidential mode" accelerator_ready
absent "no host accelerator driver loaded" lsmod_has '^nvidia'
present "input-output translation groups enumerated" test -e /dev/iommu

info "key broker"
expect "unattested fetch refused" 401 broker_probe

info "identity"
present "root certificate present" test -e "${PKI_DIR:-/var/lib/backendai-pki}/root/ca.crt"
present "services intermediate present" test -e "${PKI_DIR:-/var/lib/backendai-pki}/services/intermediate.crt"
present "standby intermediate pre-provisioned" test -e "${PKI_DIR:-/var/lib/backendai-pki}/standby/intermediate.crt"

if (( FAILED == 0 )); then
    ok "host is confidential-ready, $SKIPPED checks skipped"
else
    bad "$FAILED checks failed; this host is not confidential-ready"
    exit 1
fi
