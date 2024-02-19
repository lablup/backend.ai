python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-storage-watcher",
        description="Backend.AI Storage Watcher plugin",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_watcher_v10": {
            "storage": "ai.backend.watcher_modules.storage.watcher:StorageWatcherPlugin",
        },
        "backendai_watcher_webapp_v10": {
            "storage": "ai.backend.watcher_modules.storage.webapp:StorageWatcherWebapp",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
