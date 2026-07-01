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

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/logging/**",
    ],
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
