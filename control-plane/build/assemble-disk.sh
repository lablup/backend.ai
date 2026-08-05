#!/bin/bash
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
TREE=$(cd "${HERE}/.." && pwd)

BUNDLE=${1:?usage: assemble-disk.sh <bundle-dir> <disk> <state-key> [state-mib]}
DISK=${2:?disk image path}
KEYFILE=${3:?state disk key file}
STATE_MIB=${4:-8192}
ESP_MIB=96

ROOTHASH=$(awk '/Root hash:/ { print $3 }' "${BUNDLE}/verity.txt")
[ ${#ROOTHASH} -eq 64 ] || { echo "assemble-disk: root hash is not 32 bytes" >&2; exit 1; }

guid() {
    printf '%s-%s-%s-%s-%s' "${1:0:8}" "${1:8:4}" "${1:12:4}" "${1:16:4}" "${1:20:12}"
}
mib() {
    echo $(( ( $(stat -c %s "$1") + 1048575 ) / 1048576 ))
}

ROOT_MIB=$(mib "${BUNDLE}/rootfs.erofs")
HASH_MIB=$(mib "${BUNDLE}/rootfs.verity")

rm -f "$DISK"
truncate -s $(( (ESP_MIB + ROOT_MIB + HASH_MIB + STATE_MIB + 4) * 1048576 )) "$DISK"
sgdisk --clear \
    -n "1:1M:+${ESP_MIB}M" -t 1:EF00 -c 1:esp \
    -n "2:0:+${ROOT_MIB}M" -t 2:4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709 \
        -u "2:$(guid "${ROOTHASH:0:32}")" -c 2:root \
    -n "3:0:+${HASH_MIB}M" -t 3:2C7357ED-EBD2-46D9-AEC1-23D437EC2BF5 \
        -u "3:$(guid "${ROOTHASH:32:32}")" -c 3:root-verity \
    -n "4:0:+${STATE_MIB}M" -t 4:0FC63DAF-8483-4772-8E79-3D69D8477DE4 -c 4:backendai-state \
    "$DISK" > /dev/null

truncate -s "${ESP_MIB}M" "${BUNDLE}/esp.img"
mkfs.vfat -n ESP -F 32 "${BUNDLE}/esp.img" > /dev/null
mmd -i "${BUNDLE}/esp.img" ::/EFI ::/EFI/BOOT
mcopy -i "${BUNDLE}/esp.img" "${BUNDLE}/state-bundle.efi" ::/EFI/BOOT/BOOTX64.EFI

start() {
    sgdisk -i "$1" "$DISK" | awk '/First sector/ { print $3 }'
}

dd if="${BUNDLE}/esp.img" of="$DISK" bs=512 seek="$(start 1)" conv=notrunc,sparse status=none
dd if="${BUNDLE}/rootfs.erofs" of="$DISK" bs=512 seek="$(start 2)" conv=notrunc,sparse status=none
dd if="${BUNDLE}/rootfs.verity" of="$DISK" bs=512 seek="$(start 3)" conv=notrunc,sparse status=none

LOOP=$(losetup --find --show --offset "$(( $(start 4) * 512 ))" \
    --sizelimit "$(( STATE_MIB * 1048576 ))" "$DISK")
trap 'losetup -d "$LOOP"' EXIT
cryptsetup luksFormat --type luks2 --batch-mode --pbkdf pbkdf2 --key-file "$KEYFILE" "$LOOP"
cryptsetup luksOpen --key-file "$KEYFILE" "$LOOP" backendai-state-format
mkfs.ext4 -q -L backendai-state /dev/mapper/backendai-state-format
cryptsetup luksClose backendai-state-format

"${TREE}/bin/state-header-seal" "$LOOP" "$KEYFILE" > "${BUNDLE}/state-header-mac"
echo "assemble-disk: ${DISK} roothash=${ROOTHASH} header-mac=$(cat "${BUNDLE}/state-header-mac")"
