#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need git make curl docker python3 tar objdump
need_root "rootfs.sh"

variant="$(kata_variant_suffix)"
stage="${BAI_CC_OUT}/rootfs"
krunner="${BAI_CC_CACHE}/krunner"

checkout_kata() {
	if [ ! -d "${BAI_CC_KATA_SRC}/.git" ]; then
		git clone --filter=blob:none "${BAI_CC_KATA_REPO}" "${BAI_CC_KATA_SRC}"
	fi
	git -C "${BAI_CC_KATA_SRC}" fetch --depth 1 origin "${BAI_CC_KATA_COMMIT}"
	git -C "${BAI_CC_KATA_SRC}" checkout --force --detach "${BAI_CC_KATA_COMMIT}"
	git -C "${BAI_CC_KATA_SRC}" clean -fdx tools/packaging/kernel/configs/fragments
	fetch "${BAI_CC_KATA_VERSIONS_URL}" "${BAI_CC_CACHE}/versions.yaml" "${BAI_CC_KATA_VERSIONS_SHA256}"
	cmp -s "${BAI_CC_CACHE}/versions.yaml" "${BAI_CC_KATA_SRC}/versions.yaml" \
		|| die "kata checkout does not match the pinned release versions.yaml"
	install -D -m 0644 "${BAI_CC_ROOT}/kernel/fragments/backendai.conf" \
		"${BAI_CC_KATA_SRC}/tools/packaging/kernel/configs/fragments/common/backendai.conf"
}

upstream_rootfs_dir() {
	find "${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build/rootfs-image-${variant}" \
		-maxdepth 4 -type d -name "${BAI_CC_ROOTFS_DISTRO}_rootfs" -print -quit 2>/dev/null
}

upstream_stamp() {
	printf '%s\0' "${BAI_CC_KATA_COMMIT}" "$variant" "${BAI_CC_ROOTFS_DISTRO}" \
		"${BAI_CC_EXTRA_PKGS}" "${BAI_CC_REPO_COMPONENTS}" \
		"${BAI_CC_API_SERVER_REST_FEATURES}" "${SOURCE_DATE_EPOCH}" \
		| cat - "${BAI_CC_ROOT}/kernel/fragments/backendai.conf" | sha256sum | cut -d' ' -f1
}

build_upstream() {
	local lb="${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build"
	local stamp="${BAI_CC_CACHE}/upstream.stamp" want
	want="$(upstream_stamp)"
	if [ "${BAI_CC_FORCE_UPSTREAM:-0}" != 1 ] && [ -n "$(upstream_rootfs_dir)" ] \
		&& [ "$(cat "$stamp" 2>/dev/null)" = "$want" ]; then
		log "upstream rootfs already current for ${want}; BAI_CC_FORCE_UPSTREAM=1 rebuilds it"
		return 0
	fi
	EXTRA_PKGS="${BAI_CC_EXTRA_PKGS}" \
	REPO_COMPONENTS="${BAI_CC_REPO_COMPONENTS}" \
	API_SERVER_REST_FEATURES="${BAI_CC_API_SERVER_REST_FEATURES}" \
	SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" \
		make -C "$lb" "rootfs-image-${variant}-tarball"
	mkdir -p "$(dirname "$stamp")"
	printf '%s\n' "$want" > "$stamp"
}

stage_upstream_rootfs() {
	local built
	built="$(upstream_rootfs_dir)"
	[ -n "$built" ] || die "upstream rootfs directory not found for variant ${variant}"
	rm -rf "$stage"
	mkdir -p "$(dirname "$stage")"
	cp -a "$built" "$stage"
	[ -x "${stage}/usr/bin/kata-agent" ] || [ -L "${stage}/sbin/init" ] \
		|| die "staged rootfs carries no kata-agent"
}

stage_krunner() {
	rm -rf "$krunner"
	mkdir -p "$krunner"
	local whl="${krunner}/krunner.whl"
	fetch "${BAI_CC_KRUNNER_WHEEL_URL}" "$whl" "${BAI_CC_KRUNNER_WHEEL_SHA256}"
	python3 -m zipfile -e "$whl" "${krunner}/unpacked"
	local env_tar
	env_tar="$(find "${krunner}/unpacked" -name "krunner-env.${BAI_CC_KRUNNER_DISTRO}.${BAI_CC_TARGET_ARCH}.tar.xz" -print -quit)"
	[ -n "$env_tar" ] || die "krunner environment archive for ${BAI_CC_KRUNNER_DISTRO}/${BAI_CC_TARGET_ARCH} not in wheel"
	install -d -m 0755 "${stage}/opt/backend.ai"
	tar xJf "$env_tar" -C "${stage}/opt/backend.ai"
}

stage_runner() {
	local src="${BAI_CC_ROOT}/${BAI_CC_BACKENDAI_SRC}"
	local sp="${stage}/opt/backend.ai/lib/python${BAI_CC_KRUNNER_PYVER}/site-packages/ai/backend"
	install -d -m 0755 "$sp" "${stage}/opt/kernel"
	cp -a "${src}/kernel" "${sp}/kernel"
	cp -a "${src}/helpers" "${sp}/helpers"
	find "$sp" -name '__pycache__' -type d -prune -exec rm -rf {} +
	local arch="${BAI_CC_TARGET_ARCH}"
	install -m 0755 "${src}/runner/su-exec.${arch}.bin" "${stage}/opt/kernel/su-exec"
	install -m 0755 "${src}/runner/dropbearmulti.${arch}.bin" "${stage}/opt/kernel/dropbearmulti"
	install -m 0755 "${src}/runner/sftp-server.${arch}.bin" "${stage}/opt/kernel/sftp-server"
	install -m 0755 "${src}/runner/tmux.${arch}.bin" "${stage}/opt/kernel/tmux"
	install -m 0755 "${src}/runner/ttyd_linux.${arch}.bin" "${stage}/opt/kernel/ttyd"
	install -m 0755 "${src}/runner/all-smi.${arch}.bin" "${stage}/usr/local/bin/all-smi"
	install -m 0755 "${src}/runner/bssh.${arch}.bin" "${stage}/usr/local/bin/bssh"
	install -m 0755 "${src}/runner/entrypoint.sh" "${stage}/opt/kernel/entrypoint.sh"
	install -m 0755 "${src}/runner/yank.sh" "${stage}/opt/kernel/yank.sh"
	install -m 0644 "${src}/runner/extract_dotfiles.py" "${stage}/opt/kernel/extract_dotfiles.py"
	install -m 0644 "${src}/runner/fantompass.py" "${stage}/opt/kernel/fantompass.py"
	install -m 0644 "${src}/runner/hash_phrase.py" "${stage}/opt/kernel/hash_phrase.py"
	install -m 0644 "${src}/runner/words.json" "${stage}/opt/kernel/words.json"
	cp -a "${src}/runner/terminfo.alpine3.8" "${stage}/opt/kernel/terminfo"
}

stage_needed_libs() {
	local one="$1" obj="$2" so found rel
	for so in $(objdump -p "$obj" 2>/dev/null | awk '/NEEDED/ {print $2}'); do
		found="$(find "${one}/lib" "${one}/usr/lib" -name "$so" -print -quit 2>/dev/null)"
		[ -n "$found" ] || die "stage-one has no ${so}, needed by ${obj#"${one}"/}"
		rel="${found#"${one}"/}"
		if [ ! -e "${stage}/${rel}" ]; then
			install -D -m 0755 "$found" "${stage}/${rel}"
			stage_needed_libs "$one" "$found"
		fi
	done
}

stage_one_root() {
	local dir="${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build/rootfs-${variant}-stage-one"
	if [ -e "${dir}/usr/sbin/mount.nfs" ]; then
		printf '%s' "$dir"
		return 0
	fi
	local unpacked="${BAI_CC_CACHE}/stage-one"
	if [ ! -e "${unpacked}/usr/sbin/mount.nfs" ]; then
		[ -e "${dir}.tar.zst" ] || die "neither the stage-one tree nor its tarball is present"
		mkdir -p "$unpacked"
		tar --zstd -xf "${dir}.tar.zst" -C "$unpacked"
	fi
	printf '%s' "$unpacked"
}

stage_storage_clients() {
	local one
	one="$(stage_one_root)"
	local rel
	for rel in usr/sbin/mount.nfs usr/sbin/mount.nfs4 usr/sbin/mount.ceph usr/sbin/mount.cifs \
		usr/sbin/rpcbind usr/sbin/rpc.statd usr/bin/gocryptfs usr/bin/fusermount3 \
		usr/sbin/cryptsetup usr/sbin/dmsetup usr/sbin/mkfs.ext4 usr/sbin/blkid; do
		[ -e "${one}/${rel}" ] || die "stage-one carries no ${rel}"
		install -D -m 0755 "${one}/${rel}" "${stage}/${rel}"
		stage_needed_libs "$one" "${one}/${rel}"
	done
}

stage_fuse_driver() {
	local src out built
	src="$(cd "${BAI_CC_ROOT}/../rust" && pwd)"
	out="${BAI_CC_CACHE}/rust"
	built="${out}/target/${BAI_CC_RUST_TARGET}/release/bai-storage-fuse"
	mkdir -p "$out"
	docker run --rm --platform "${BAI_CC_RUST_PLATFORM}" \
		-v "${src}:/src:ro" -v "${out}:/out" \
		-e CARGO_HOME=/out/cargo -e CARGO_TARGET_DIR=/out/target \
		-e SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" \
		"${BAI_CC_RUST_IMAGE}" \
		cargo build --locked --manifest-path /src/Cargo.toml \
			-p bai-storage-fuse --release --target "${BAI_CC_RUST_TARGET}"
	[ -x "$built" ] || die "the confidential storage driver did not build"
	if objdump -p "$built" | grep -q NEEDED; then
		die "bai-storage-fuse links against shared libraries; the staged driver must be static"
	fi
	install -D -m 0755 "$built" "${stage}/usr/local/bin/bai-storage-fuse"
}

stage_tunnel() {
	local one rel
	one="$(stage_one_root)"
	for rel in ${BAI_CC_TUNNEL_BINS}; do
		[ -e "${one}/${rel}" ] || die "stage-one carries no ${rel}, needed by the inter-kernel tunnel"
		install -D -m 0755 "${one}/${rel}" "${stage}/${rel}"
		stage_needed_libs "$one" "${one}/${rel}"
	done
}

stage_overlay() {
	cp -a "${BAI_CC_ROOT}/overlay/." "${stage}/"
	find "${stage}/opt/kernel" "${stage}/usr/local/bin" -name '__pycache__' -type d -prune -exec rm -rf {} +
	chmod 0755 "${stage}/opt/kernel/bai-cc-entrypoint" "${stage}/usr/local/bin/bai-guest-boot" \
		"${stage}/usr/local/bin/bai-guest-storage" \
		"${stage}/usr/local/bin/bai-tunnel-up" "${stage}/opt/kernel/bai-tunnel-bench"
	install -d -m 0755 "${stage}/usr/lib/systemd/system/multi-user.target.wants"
	ln -sf ../bai-guest-boot.service "${stage}/usr/lib/systemd/system/multi-user.target.wants/bai-guest-boot.service"
	ln -sf ../bai-tunnel-up.path "${stage}/usr/lib/systemd/system/multi-user.target.wants/bai-tunnel-up.path"
	rm -f "${stage}"/opt/kernel/libbaihook.*.so "${stage}"/opt/kernel/jail.*.bin
}

checkout_kata
build_upstream
stage_upstream_rootfs
stage_krunner
stage_runner
stage_storage_clients
stage_fuse_driver
stage_tunnel
stage_overlay
canonicalise_tree "$stage"
mkdir -p "${BAI_CC_OUT}"
canonical_tar "$stage" "${BAI_CC_OUT}/rootfs.tar"
log "staged rootfs $(sha256_of "${BAI_CC_OUT}/rootfs.tar")"
