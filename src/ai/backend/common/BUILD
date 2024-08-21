python_sources(
    name="src",
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/manager/**",
        "//src/ai/backend/agent/**",
        "//src/ai/backend/client/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/storage/**",
        "//src/ai/backend/web/**",
        "//src/ai/backend/accelerator/**",
        "//src/ai/backend/test/**",
        "//src/ai/backend/testutils/**",
        "//src/ai/backend/install/**",
        "//src/ai/backend/wsproxy/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/plugin/**",
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
