python_sources(
    name="lib",
    dependencies=[
        ":resources",
    ],
)

# This distribution is not actually uploaded to PyPI.
# We have separate krunner static distributions.
python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-krunner-runtime",
        description="Backend.AI Kernel Runner Prebuilt Binaries Package",
        license="LGPLv3",
    ),
    generate_setup=True,
    repositories=[
        "@pypi",
    ],
)

resource(name="version", source="VERSION")

resources(
    name="resources",
    dependencies=[
        ":version",
        ":platform-binaries",
    ],
    sources=[
        "*.sh",
        "*.svg",
        "*.md",
    ],
)

platform_resources(
    name="platform-binaries",
    dependency_map={
        "linux_x86_64": ":linux-x86_64-binaries",
        "linux_arm64": ":linux-arm64-binaries",
    },
)

resources(
    name="linux-x86_64-binaries",
    sources=[
        "*.x86_64.bin",
        "*.x86_64.so",
        "*.x86_64.tar.xz",
    ],
)

resources(
    name="linux-arm64-binaries",
    sources=[
        "*.aarch64.bin",
        "*.aarch64.so",
        "*.aarch64.tar.xz",
    ],
)
