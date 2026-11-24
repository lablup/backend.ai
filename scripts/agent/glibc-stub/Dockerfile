FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS build
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    gcc-x86-64-linux-gnu libc6-dev-amd64-cross \
    gcc-aarch64-linux-gnu libc6-dev-arm64-cross
WORKDIR /build
# The libraries are empty: since glibc 2.34 the real implementations live in libc.so.6.
# The loader fails when a version name that the Python needs is not in versions.map.
COPY versions.map ./
RUN set -e; \
  for arch in x86_64 aarch64; do \
    for library in libdl.so.2 libpthread.so.0 librt.so.1 libutil.so.1; do \
      "${arch}-linux-gnu-gcc" -shared -nostdlib -s \
        -Wl,-soname,"${library}" -Wl,--version-script=versions.map \
        -Wl,--build-id=none -Wl,-z,noexecstack -Wl,--no-as-needed \
        -o "glibc-stub.${library}.${arch}.so" -x c /dev/null -lc; \
    done; \
  done

FROM scratch
COPY --from=build /build/*.so /
