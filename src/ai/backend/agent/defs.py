from typing import Final

KRUNNER_ENTRYPOINT_GROUP: Final[str] = "backendai_krunner_v10"
FALLBACK_KERNEL_PYTHON_VERSION: Final[str] = "3.6"  # Need to update?
<<<<<<< HEAD
=======
SESSION_NAME_CONFIG_FILENAME: Final[str] = "session_name.txt"

# Libraries that became empty stubs in glibc 2.34, and that minimal images leave out.
GLIBC_STUB_LIBRARIES: Final[tuple[str, ...]] = (
    "libdl.so.2",
    "libpthread.so.0",
    "librt.so.1",
    "libutil.so.1",
)
# The path is also written in runner/entrypoint.sh.
GLIBC_STUB_CONTAINER_DIR: Final[str] = "/opt/kernel/glibc-stub"
>>>>>>> 8eee639c4 (fix(BAI-919): load the krunner Python on images without glibc stubs (#17307))
