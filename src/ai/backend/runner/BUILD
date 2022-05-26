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
        ":linux-x86_64-target",
        ":linux-arm64-target",
    ],
    sources=[
        "*.sh",
        "*.svg",
        "*.md",
    ],
)

target(
    name="linux-x86_64-target",
    platform="linux_x86_64",
    platform_dependencies=[
        ":linux-x86_64-binaries",
    ],
)
target(
    name="linux-arm64-target",
    platform="linux_arm64",
    platform_dependencies=[
        ":linux-arm64-binaries",
    ],
)

# target(
#     name="platform-binaries",
#     platforms={
#         "linux-x86_64": ":linux-x86_64-binaries",
#         "linux-arm64": ":linux-arm64-binaries",
#     },
# )

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
