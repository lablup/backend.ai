python_tests(
    name="tests",
    # The seed sync test reads the fixture it is held against; nothing infers a path.
    dependencies=["fixtures/manager:json"],
    overrides={
        # Imports every entity type module by walking the package.
        "test_put_every_entity_in_the_graph.py": {
            "dependencies": ["src/ai/backend/common:src"],
        },
    },
)
