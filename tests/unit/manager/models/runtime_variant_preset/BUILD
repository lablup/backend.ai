python_tests(
    name="tests",
    # The seed sources are read as data rather than imported, so the
    # dependencies cannot be inferred.
    dependencies=[
        "fixtures/manager:json",
        "src/ai/backend/manager/models/alembic/versions/e7b3a1f9c2d4_seed_runtime_variant_presets_data.py:../../../src",
        "src/ai/backend/manager/models/alembic/versions/fb5befb44035_seed_enable_prompt_tokens_details_preset.py:../../../src",
    ],
)
