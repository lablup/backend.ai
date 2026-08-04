#!/usr/bin/env bash
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"

need git make curl docker python3 tar
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

build_upstream() {
	local lb="${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build"
	EXTRA_PKGS="${BAI_CC_EXTRA_PKGS}" \
	REPO_COMPONENTS="${BAI_CC_REPO_COMPONENTS}" \
	API_SERVER_REST_FEATURES="${BAI_CC_API_SERVER_REST_FEATURES}" \
	SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" \
		make -C "$lb" "kernel-${variant}-tarball" "rootfs-image-${variant}-tarball"
}

stage_upstream_rootfs() {
	local built
	built="$(find "${BAI_CC_KATA_SRC}/tools/packaging/kata-deploy/local-build/build/rootfs-image-${variant}" \
		-maxdepth 4 -type d -name "${BAI_CC_ROOTFS_DISTRO}_rootfs" -print -quit)"
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
	python3 -m pip download --no-deps --only-binary=:all: --dest "$krunner" "${BAI_CC_KRUNNER_REQUIREMENT}"
	local whl
	whl="$(find "$krunner" -name '*.whl' -print -quit)"
	[ -n "$whl" ] || die "krunner wheel not downloaded"
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

stage_overlay() {
	cp -a "${BAI_CC_ROOT}/overlay/." "${stage}/"
	chmod 0755 "${stage}/opt/kernel/bai-cc-entrypoint" "${stage}/usr/local/bin/bai-guest-boot"
	install -d -m 0755 "${stage}/usr/lib/systemd/system/multi-user.target.wants"
	ln -sf ../bai-guest-boot.service "${stage}/usr/lib/systemd/system/multi-user.target.wants/bai-guest-boot.service"
	rm -f "${stage}"/opt/kernel/libbaihook.*.so "${stage}"/opt/kernel/jail.*.bin
}

checkout_kata
build_upstream
stage_upstream_rootfs
stage_krunner
stage_runner
stage_overlay
canonicalise_tree "$stage"
mkdir -p "${BAI_CC_OUT}"
canonical_tar "$stage" "${BAI_CC_OUT}/rootfs.tar"
log "staged rootfs $(sha256_of "${BAI_CC_OUT}/rootfs.tar")"
