#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"

KATA_VERSION="${KATA_VERSION:-3.31.0}"
NERDCTL_VERSION="${NERDCTL_VERSION:-2.3.5}"
KATA_DIR=/opt/kata/share/defaults/kata-containers
COCO_MODE=/home/devops/coco/tools/coco-mode
GPU_ID=10de:2bb5
MODELS_IMG="${MODELS_IMG:-/data/models.img}"
REGISTRY_ADDR="${REGISTRY_ADDR:-10.4.0.1}"
REGISTRY_CERTS="${REGISTRY_CERTS:-/opt/coco/cc-c4/certs}"
ATTESTATION_KEY=0C0E6AF955CE463C03FC51574D098D70AFBE5E1F
REBOOT_REQUIRED=0

apt_install() { DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@" >/dev/null; }
installed() { local p; for p in "$@"; do dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q '^install ok installed' || return 1; done; }
kernel_says() { journalctl -k -b | grep -q "$1"; }
needs_reboot() { REBOOT_REQUIRED=1; warn "$* — reboot is the owner's, over the out-of-band controller"; }

require_firmware() {
    local missing=0
    kernel_says 'x86/tme: enabled by BIOS' || { bad "memory encryption is off in firmware"; missing=1; }
    kernel_says 'virt/tdx: BIOS enabled' || { bad "trusted domain extensions are off in firmware"; missing=1; }
    [[ -e /dev/sgx_provision ]] || { bad "software guard extensions are off in firmware, and trusted domain extensions do not un-gray without them"; missing=1; }
    kernel_says 'SEAMCALL.*failed' && { bad "the secure-arbitration module reported a call failure this boot"; missing=1; } || true
    (( missing == 0 )) || die "firmware settings are set by hand over the out-of-band controller and cannot be applied from here"
    ok "firmware gate"
}

check_hibernation() { grep -qw nohibernate /proc/cmdline; }
apply_hibernation() {
    grep -q 'GRUB_CMDLINE_LINUX=.*nohibernate' /etc/default/grub \
        || sed -i -E 's|^(GRUB_CMDLINE_LINUX=")|\1nohibernate |' /etc/default/grub
    update-grub >/dev/null
    needs_reboot "hibernation must be off before the module initialises"
}

check_tdx_module() { [[ $(cat /sys/module/kvm_intel/parameters/tdx 2>/dev/null) == Y ]] && kernel_says 'virt/tdx: module initialized'; }
apply_tdx_module() {
    printf 'options kvm_intel tdx=1\n' >/etc/modprobe.d/kvm-intel-tdx.conf
    needs_reboot "the module arms lazily when the virtualisation driver loads"
}

check_expander_memory() { [[ -e /etc/modprobe.d/blacklist-kmem.conf ]] && ! kernel_says 'TDX_PAMT_OUTSIDE_CMRS'; }
apply_expander_memory() {
    printf 'blacklist kmem\n' >/etc/modprobe.d/blacklist-kmem.conf
    needs_reboot "the memory expander must not be onlined as system memory"
}

check_hypervisor() { installed qemu-system-x86 qemu-utils ovmf ovmf-inteltdx && [[ -e /usr/share/ovmf/OVMF.inteltdx.ms.fd ]]; }
apply_hypervisor() {
    apt_install qemu-system-x86 qemu-utils ovmf ovmf-inteltdx cloud-image-utils genisoimage
    usermod -aG kvm "${SUDO_USER:-devops}"
}

check_vhost_net() { lsmod | grep -qw vhost_net && [[ -e /etc/modules-load.d/vhost-net.conf ]]; }
apply_vhost_net() { modprobe vhost_net; printf 'vhost_net\n' >/etc/modules-load.d/vhost-net.conf; }

check_attestation_source() { [[ -e /etc/apt/keyrings/kobuk-tdx-attestation.gpg && -e /etc/apt/sources.list.d/kobuk-tdx-attestation-noble.sources ]]; }
apply_attestation_source() {
    mkdir -p /etc/apt/keyrings
    curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x$ATTESTATION_KEY" \
        | gpg --dearmor -o /etc/apt/keyrings/kobuk-tdx-attestation.gpg
    cat >/etc/apt/sources.list.d/kobuk-tdx-attestation-noble.sources <<'EOF'
Types: deb
URIs: https://ppa.launchpadcontent.net/kobuk-team/tdx-attestation-release/ubuntu
Suites: noble
Components: main
Signed-By: /etc/apt/keyrings/kobuk-tdx-attestation.gpg
EOF
    apt-get update >/dev/null
}

check_quoting() { installed tdx-qgs libsgx-dcap-default-qpl sgx-dcap-pccs libsgx-dcap-quote-verify && systemctl is-active --quiet qgsd; }
apply_quoting() { apt_install tdx-qgs libsgx-dcap-default-qpl sgx-dcap-pccs libsgx-dcap-quote-verify; }

check_caching_service() {
    local client=/opt/intel/sgx-dcap-pccs/pcs_client/pcs_client.js
    [[ -r $client ]] || return 1
    ! grep -q "Ocp-Apim-Subscription-Key" "$client" \
        && [[ $(curl -ks -o /dev/null -w '%{http_code}' https://localhost:8081/sgx/certification/v4/rootcacrl) == 200 ]]
}
apply_caching_service() {
    sed -i.bak \
        -e "s|headers: { 'Ocp-Apim-Subscription-Key': Config.get('ApiKey') },|headers: {},|" \
        -e "/^      'Ocp-Apim-Subscription-Key': Config.get('ApiKey'),$/d" \
        /opt/intel/sgx-dcap-pccs/pcs_client/pcs_client.js
    systemctl restart pccs
    sleep 5
}

registered() {
    [[ -e /var/log/mpa_registration.log ]] && grep -q 'passed successfully' /var/log/mpa_registration.log && return 0
    installed sgx-ra-service && mpa_manage -get_registration_status 2>/dev/null | grep -q 'completed successfully'
}

platform_registration() {
    if registered; then
        ok "platform registration (already fired; nothing is sent)"
        return 0
    fi
    if [[ -e $(done_marker platform_registration) ]]; then
        die "this host has a registration marker dated $(cat "$(done_marker platform_registration)") but no evidence of a completed registration; investigate by hand, do not re-fire"
    fi
    bad "PLATFORM REGISTRATION HAS NOT FIRED ON THIS HOST"
    cat >&2 <<'EOF'

Installing sgx-ra-service sends this machine's platform manifest to Intel's registration
service, from the package post-install script, about two seconds after the install begins.
There is no later confirmation step and no way to stop it once apt has started.

The action is IRREVERSIBLE. It cannot be undone, retracted or repeated safely, and it is a
transaction with a third party rather than a change to this machine. On the rig it already
fired at 2026-07-21 04:44:22 UTC and must never be fired again.

Nothing else in this recipe does anything irreversible. Every other step is a local change
you can put back.

Proceed only if you are provisioning a genuinely new, never-registered machine.

EOF
    if [[ ${ALLOW_PLATFORM_REGISTRATION:-0} != 1 ]]; then
        warn "skipping; re-run with ALLOW_PLATFORM_REGISTRATION=1 on a machine that has never been registered"
        return 0
    fi
    confirm_exact "register $(hostname) with Intel irreversibly on $(date +%Y-%m-%d)"
    ledger "IRREVERSIBLE platform registration fired for $(hostname)"
    mark_done platform_registration
    apt_install sgx-ra-service
    sleep 5
    registered || bad "the agent did not report success; read /var/log/mpa_registration.log and do not re-run"
}

check_kata() { [[ $(/opt/kata/bin/kata-runtime --version 2>/dev/null | head -1) == *"$KATA_VERSION"* ]]; }
apply_kata() {
    local tarball="/tmp/kata-static-$KATA_VERSION-amd64.tar.zst"
    [[ -e $tarball ]] || curl -fsSL -o "$tarball" \
        "https://github.com/kata-containers/kata-containers/releases/download/$KATA_VERSION/kata-static-$KATA_VERSION-amd64.tar.zst"
    tar --zstd -xf "$tarball" -C /
}

check_kata_config() {
    grep -q '^experimental_force_guest_pull = true' "$KATA_DIR/configuration-qemu-tdx.toml" \
        && grep -q '^experimental_force_guest_pull = true' "$KATA_DIR/configuration-qemu-nvidia-gpu-tdx.toml" \
        && grep -q '^pod_resource_api_sock = ""' "$KATA_DIR/configuration-qemu-nvidia-gpu-tdx.toml"
}
apply_kata_config() {
    sed -i 's/^experimental_force_guest_pull = false/experimental_force_guest_pull = true/' \
        "$KATA_DIR/configuration-qemu-tdx.toml" "$KATA_DIR/configuration-qemu-nvidia-gpu-tdx.toml"
    sed -i 's|^pod_resource_api_sock = .*|pod_resource_api_sock = ""|' \
        "$KATA_DIR/configuration-qemu-nvidia-gpu-tdx.toml"
}

shim_for() { printf '/usr/local/bin/containerd-shim-kata-%s-v2' "$1"; }
check_shims() {
    local handler config
    while read -r handler config; do
        grep -q "KATA_CONF_FILE=$KATA_DIR/$config" "$(shim_for "$handler")" 2>/dev/null || return 1
    done <<<"$(shim_table)"
}
shim_table() {
    printf 'qemu-tdx configuration-qemu-tdx.toml\n'
    printf 'qemu-nvidia-gpu-tdx configuration-qemu-nvidia-gpu-tdx.toml\n'
    printf 'qemu configuration-qemu.toml\n'
}
apply_shims() {
    local handler config path
    while read -r handler config; do
        path=$(shim_for "$handler")
        printf '#!/bin/sh\nexport KATA_CONF_FILE=%s/%s\nexec /opt/kata/bin/containerd-shim-kata-v2 "$@"\n' \
            "$KATA_DIR" "$config" >"$path"
        chmod +x "$path"
    done <<<"$(shim_table)"
}

check_container_runtime() { installed docker.io docker-compose-v2 && systemctl is-active --quiet containerd; }
apply_container_runtime() {
    installed docker-ce && die "docker-ce is installed; its containerd would displace the 2.x the runtime needs"
    apt_install docker.io docker-compose-v2
    usermod -aG docker "${SUDO_USER:-devops}"
}

check_nerdctl() { [[ $(nerdctl --version 2>/dev/null) == *"$NERDCTL_VERSION"* ]] && [[ -e /opt/cni/bin/bridge ]]; }
apply_nerdctl() {
    local tarball="/tmp/nerdctl-full-$NERDCTL_VERSION-linux-amd64.tar.gz"
    [[ -e $tarball ]] || curl -fsSL -o "$tarball" \
        "https://github.com/containerd/nerdctl/releases/download/v$NERDCTL_VERSION/nerdctl-full-$NERDCTL_VERSION-linux-amd64.tar.gz"
    tar -C /usr/local -xzf "$tarball" bin/nerdctl
    mkdir -p /opt/cni/bin
    tar -C /opt/cni/bin --strip-components=2 -xzf "$tarball" libexec/cni
}

check_registry_certs() { [[ -e $REGISTRY_CERTS/registry.crt && -e $REGISTRY_CERTS/registry.key ]]; }
apply_registry_certs() {
    mkdir -p "$REGISTRY_CERTS"
    (umask 077; openssl req -x509 -newkey rsa:3072 -nodes -days 730 -sha256 \
        -keyout "$REGISTRY_CERTS/registry.key" -out "$REGISTRY_CERTS/registry.crt" \
        -subj "/CN=$REGISTRY_ADDR" \
        -addext "subjectAltName=IP:$REGISTRY_ADDR,IP:127.0.0.1" >/dev/null 2>&1)
}

check_registry() {
    [[ $(nerdctl inspect registry --format '{{.State.Status}}' 2>/dev/null) == running ]] \
        && [[ $(nerdctl inspect registry --format '{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null) == always ]]
}
apply_registry() {
    nerdctl rm -f registry >/dev/null 2>&1 || true
    mkdir -p /data/registry
    nerdctl run -d --name registry --net host --restart always \
        -v "$REGISTRY_CERTS:/certs:ro" \
        -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registry.crt \
        -e REGISTRY_HTTP_TLS_KEY=/certs/registry.key \
        -v /data/registry:/var/lib/registry \
        docker.io/library/registry:2 >/dev/null
}

check_models_loop() {
    [[ ! -e $MODELS_IMG ]] && return 0
    systemctl is-enabled --quiet backendai-coco-models.service && losetup -j "$MODELS_IMG" | grep -q .
}
apply_models_loop() {
    [[ -e $MODELS_IMG ]] || { warn "no model image at $MODELS_IMG; nothing to attach"; return 0; }
    cat >/etc/systemd/system/backendai-coco-models.service <<EOF
[Unit]
Description=Attach the model image as a loop device for confidential sessions
After=local-fs.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/losetup -f --show $MODELS_IMG
ExecStop=/bin/sh -c '/sbin/losetup -d \$(/sbin/losetup -j $MODELS_IMG | cut -d: -f1)'

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable --now backendai-coco-models.service
}

check_accelerator() {
    local status bound total on queried
    status=$("$COCO_MODE" status 2>/dev/null) || return 1
    bound=$(grep -c 'driver=vfio-pci' <<<"$status" || true)
    total=$(grep -c 'driver=' <<<"$status" || true)
    on=$(grep -c 'CC mode is on' <<<"$status" || true)
    queried=$(grep -c 'CC mode is ' <<<"$status" || true)
    (( total > 0 && bound == total && queried > 0 && on == queried ))
}
apply_accelerator() {
    "$COCO_MODE" on || die "the accelerator mode script refused; read its output rather than binding anything by hand"
    check_accelerator || needs_reboot "the accelerator staging needs a boot before it takes"
}

as_root
[[ ${1:-} == --dry-run ]] && DRY_RUN=1
info "provisioning $(hostname); every step checks before it acts"
require_firmware
for name in hibernation tdx_module expander_memory hypervisor vhost_net \
            attestation_source quoting caching_service; do
    step "$name"
done
platform_registration
for name in kata kata_config shims container_runtime nerdctl \
            registry_certs registry models_loop accelerator; do
    step "$name"
done
(( REBOOT_REQUIRED == 0 )) || die "staged changes need a reboot; the owner reboots over the out-of-band controller, then re-run this script"
ok "provisioning complete; run $HERE/verify.sh to inspect the result"
