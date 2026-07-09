python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        ":resources",
        "//:reqs#authlib",  # pants: no-infer-dep in plugin/openid/webapp.py
        "//:reqs#httpx",  # pants: no-infer-dep in plugin/openid/webapp.py (authlib dep)
    ],
)

# Per-layer dependency direction (bottom -> top): data -> views -> models.
# Each rule set is self-contained: the upper-layer denies come first, then the same
# base allowances as the default set. Paths starting with "/" are relative to this
# (manager) directory; "//" is relative to the build root.
__dependencies_rules__(
    # data: must not depend on views, models, repositories, services, api.
    (
        "/data/**",
        "!/views/**",
        "!/models/**",
        "!/repositories/**",
        "!/services/**",
        "!/api/**",
        "/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/logging/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
    # views: must not depend on models, repositories, services, api.
    (
        "/views/**",
        "!/models/**",
        "!/repositories/**",
        "!/services/**",
        "!/api/**",
        "/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/logging/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
    # models: may depend on views/data; must not depend on repositories, services, api.
    (
        "/models/**",
        "!/repositories/**",
        "!/services/**",
        "!/api/**",
        "/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/logging/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
    # default: every other file in the component (matches the old macro behavior).
    (
        "*",
        "/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/logging/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
)

# Who may import the manager component (equivalent to visibility_private_component).
__dependents_rules__(
    (
        {"type": "*"},
        "/**",  # code within this component may import itself
        "//src/ai/backend/testutils/**",  # allowed extra dependents
        "//tests/**",  # tests may import the source files
        "//plugins/**",  # external plugins may import the source files
        "!*",  # no one else may import the source files
    )
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-manager",
        description="Backend.AI Manager",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "mgr": "ai.backend.manager.cli.__main__:main",
            "mgr.start-server": "ai.backend.manager.cli.start_server:main",
        },
        "backendai_error_monitor_v20": {
            "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorMonitor",
        },
        "backendai_event_dispatcher_v20": {
            "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorEventDispatcher",
        },
        "backendai_hook_v20": {
            "totp": "ai.backend.manager.plugin.totp.hook:TOTPHook",
            "openid": "ai.backend.manager.plugin.openid.hook:OIDCHookPlugin",
            "auth_keypair": "ai.backend.manager.plugin.keypair.hook:KeypairAuthHookPlugin",
        },
        "backendai_webapp_v20": {
            "totp": "ai.backend.manager.plugin.totp.webapp:TOTPWebapp",
            "openid": "ai.backend.manager.plugin.openid.webapp:OIDCWebAppPlugin",
            "auth_keypair": "ai.backend.manager.plugin.keypair.webapp:KeypairAuthWebAppPlugin",
        },
        "backendai_network_manager_v1": {
            "overlay": "ai.backend.manager.network.overlay:OverlayNetworkPlugin",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="backendai-manager",
    **common_scie_config("lazy"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-manager-fat",
    **common_scie_config("eager"),
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-manager*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-manager",
        ":backendai-manager-fat",
    ],
    tags=["checksum"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="vendor",
    sources=[
        "vendor/*",
        "vendor/**/*",
    ],
)
resources(
    name="resources",
    dependencies=[
        ":version",
        ":vendor",
    ],
    sources=[
        "**/py.typed",
        "**/*.yaml",
        "models/alembic/script.py.mako",
        "models/alembic/revision_history/*.json",
    ],
)
