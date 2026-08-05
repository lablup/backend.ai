#!/bin/bash
set -euo pipefail

DISK=${1:?usage: run-state-cvm.sh <disk> [console-log]}
LOG=${2:-/tmp/state-cvm-console.log}
QEMU=${BAI_QEMU:-/opt/kata/bin/qemu-system-x86_64-tdx-experimental}
FIRMWARE=${BAI_FIRMWARE:-/opt/kata/share/ovmf/OVMF.inteltdx.fd}
MEMORY=${BAI_MEMORY:-8192}
CPUS=${BAI_CPUS:-4}

args=(
    -name backendai-state-bundle
    -uuid "${BAI_UUID:-6f9c1d2e-4a3b-4c5d-8e7f-0a1b2c3d4e5f}"
    -machine q35,accel=kvm,kernel_irqchip=split,confidential-guest-support=tdx
    -cpu host,pmu=off
    -smp "$CPUS"
    -m "${MEMORY}M"
    -object memory-backend-ram,id=dimm0,size="${MEMORY}M"
    -numa node,memdev=dimm0
    -object '{"qom-type":"tdx-guest","id":"tdx","quote-generation-socket":{"type":"vsock","cid":"2","port":"4050"}}'
    -bios "$FIRMWARE"
    -drive "id=state,file=${DISK},format=raw,if=none"
    -device virtio-blk-pci,drive=state,serial=state
    -netdev user,id=net0
    -device virtio-net-pci,netdev=net0
    -serial "file:${LOG}"
    -display none -nodefaults -no-user-config -vga none --no-reboot
    -pidfile "${LOG}.pid"
)

if [ -n "${BAI_DIRECT_BOOT:-}" ]; then
    BUNDLE=$(cd "$(dirname "$DISK")" && pwd)/bundle
    args+=(-kernel "${BUNDLE}/vmlinuz" -initrd "${BUNDLE}/initrd.img"
           -append "$(cat "${BUNDLE}/cmdline")")
fi

exec "$QEMU" "${args[@]}"
