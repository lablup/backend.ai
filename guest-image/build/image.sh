#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need mkfs.ext4 veritysetup sgdisk truncate dd du
need_root "image.sh"

stage="${BAI_CC_OUT}/rootfs"
work="${BAI_CC_OUT}/image"
[ -d "$stage" ] || die "no staged rootfs; run build/rootfs.sh first"

align_up() { echo $(((($1 + $2 - 1) / $2) * $2)); }

rm -rf "$work"
mkdir -p "$work"

bs="${BAI_CC_BLOCK_SIZE}"
align=$((BAI_CC_IMAGE_ALIGN_MB * 1024 * 1024))
content=$(du -sb --apparent-size "$stage" | cut -f1)
data_bytes=$(align_up $(( content + content / 4 + BAI_CC_ROOT_FREE_SPACE_MB * 1024 * 1024 )) "$align")
data_blocks=$((data_bytes / bs))
hash_bytes=$(align_up $(( data_bytes / 128 + data_bytes / 16384 + 1048576 )) $((1024 * 1024)))
[ "$hash_bytes" -ge 4194304 ] || hash_bytes=4194304

truncate -s "$data_bytes" "${work}/data.img"
mkfs.ext4 -q -F -b "$bs" -m 3 \
	-U "${BAI_CC_FS_UUID}" -E "hash_seed=${BAI_CC_FS_HASH_SEED}" \
	-d "$stage" "${work}/data.img" "$data_blocks"

truncate -s "$hash_bytes" "${work}/hash.img"
verity_out="$(veritysetup format --no-superblock --hash sha256 \
	--salt "${BAI_CC_VERITY_SALT}" \
	--data-block-size "$bs" --hash-block-size "$bs" \
	--data-blocks "$data_blocks" \
	"${work}/data.img" "${work}/hash.img")"
root_hash="$(printf '%s\n' "$verity_out" | awk '/^Root hash:/ {print $3}')"
[ -n "$root_hash" ] || die "veritysetup produced no root hash"

part_start=$((2 * 1024 * 1024))
total=$(( part_start + data_bytes + hash_bytes + 2 * 1024 * 1024 ))
image="${BAI_CC_OUT}/kata-containers-backendai.img"
rm -f "$image"
truncate -s "$total" "$image"
sgdisk --clear --disk-guid="${BAI_CC_GPT_DISK_GUID}" \
	--new=1:$((part_start / 512)):+$((data_bytes / 512)) \
	--partition-guid=1:"${BAI_CC_GPT_PART1_GUID}" --change-name=1:rootfs \
	--new=2:$(((part_start + data_bytes) / 512)):+$((hash_bytes / 512)) \
	--partition-guid=2:"${BAI_CC_GPT_PART2_GUID}" --change-name=2:hash \
	"$image" >/dev/null
dd if="${work}/data.img" of="$image" bs=1M seek=2 conv=notrunc status=none
dd if="${work}/hash.img" of="$image" bs=1M seek=$((2 + data_bytes / 1048576)) conv=notrunc status=none

printf 'root_hash=%s,salt=%s,data_blocks=%s,data_block_size=%s,hash_block_size=%s\n' \
	"$root_hash" "${BAI_CC_VERITY_SALT}" "$data_blocks" "$bs" "$bs" \
	> "${BAI_CC_OUT}/kernel_verity_params.txt"

kernel="$(find "${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build/kernel-${BAI_CC_KERNEL_FLAVOUR}" \
	-name 'vmlinuz*.container' -print -quit 2>/dev/null)"
[ -n "$kernel" ] || die "no vmlinuz*.container under kernel-${BAI_CC_KERNEL_FLAVOUR}"
cp -f "$kernel" "${BAI_CC_OUT}/vmlinuz.container"

log "image $(sha256_of "$image")"
log "$(cat "${BAI_CC_OUT}/kernel_verity_params.txt")"
