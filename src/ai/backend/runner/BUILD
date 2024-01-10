python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/kernel/**",
        "//src/ai/backend/agent/**",
    ],
    allowed_dependencies=[],
)

pex_binary(
    name="extract-dotfiles",
    entry_point="extract_dotfiles.py",
)

# This package does not have external requirements.
python_requirements()

python_distribution(
    name="dist",
    dependencies=[
        ":src",
    ],
    provides=python_artifact(
        name="backend.ai-kernel-binary",
        description="Backend.AI Kernel Runner Prebuilt Binaries Package",
        license="LGPLv3",
    ),
    generate_setup=True,
    tags=["wheel", "platform-specific"],
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
        "*.css",
        "*.ttf",
        "*.dockerfile",
        "*.json",
        ".bash_profile",
        ".bashrc",
        ".zshrc",
        ".tmux.conf",
        ".vimrc",
        "terminfo.alpine3.8/**/*",
    ],
)

platform_resources(
    name="platform-binaries",
    dependency_map={
        "linux_x86_64": ":linux-x86_64-binaries",
        "linux_arm64": ":linux-arm64-binaries",
        "macos_x86_64": ":linux-x86_64-binaries",
        "macos_arm64": ":linux-arm64-binaries",
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
