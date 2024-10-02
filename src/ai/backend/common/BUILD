python_sources(
    name="src",
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/gateway/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/agent/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "src/ai/backend/common/plugin:src",
        "src/ai/backend/common/auth:src",
        "src/ai/backend/common/web/session:src",  # not auto-inferred
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
    ),
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")

resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
