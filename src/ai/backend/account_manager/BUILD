python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/account_manager/cli:src",  # not auto-inferred (due to lazy-loading cmdgroup)
        "src/ai/backend/account_manager/models/alembic:migrations",  # not auto-inferred
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/web/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
        "!//src/ai/backend/client/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-account-manager",
        description="Backend.AI Account Manager",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "am": "ai.backend.account_manager.cli.__main__:main",
            "am.start-server": "ai.backend.account_manager.server:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="pex",
    entry_point="ai.backend.cli.__main__",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-account-manager",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-account-manager-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-account-manager-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-account-manager",
        ":backendai-account-manager-fat",
    ],
    tags=["checksum"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
        ":vendor",
    ],
    sources=[
        "**/py.typed",
    ],
)
