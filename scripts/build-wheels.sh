#! /bin/bash
set -e

pants export --resolve=python-default

# Normalize the package version
PKGVER=$(./py -c "import packaging.version,pathlib; print(str(packaging.version.Version(pathlib.Path('VERSION').read_text())))")
# Build non-platform-specific wheels
pants --platform-specific-resources-target=linux_x86_64 --tag="wheel" --tag="-platform-specific" package '::'
# Build x86_64 wheels
MANYLINUX_PTAG=manylinux2014_x86_64
MACOS_PTAG=macosx_11_0_x86_64
pants --platform-specific-resources-target=linux_x86_64 --tag="wheel" --tag="+platform-specific" package '::'
for pkgname in "kernel_binary"; do
    mv "dist/backend_ai_${pkgname}-${PKGVER}-py3-none-any.whl" \
        "dist/backend_ai_${pkgname}-${PKGVER}-py3-none-${MANYLINUX_PTAG}.${MACOS_PTAG}.whl"
done
# Build arm64 wheels
MANYLINUX_PTAG=manylinux2014_aarch64
MACOS_PTAG=macosx_11_0_arm64
pants --platform-specific-resources-target=linux_arm64 --tag="wheel" --tag="+platform-specific" package '::'
for pkgname in "kernel_binary"; do
    mv "dist/backend_ai_${pkgname}-${PKGVER}-py3-none-any.whl" \
        "dist/backend_ai_${pkgname}-${PKGVER}-py3-none-${MANYLINUX_PTAG}.${MACOS_PTAG}.whl"
done

ls -lh dist
