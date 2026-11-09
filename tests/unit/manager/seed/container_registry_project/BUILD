python_tests(
    dependencies=[
        # `ensure_all_tables_registered` imports every model by name; dependency inference
        # does not see it.
        "src/ai/backend/manager:src",
    ],
)
