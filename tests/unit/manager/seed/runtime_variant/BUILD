python_tests(
    dependencies=[
        # `ensure_all_tables_registered` imports every model by name, which dependency
        # inference cannot see.
        "src/ai/backend/manager:src",
    ],
)

python_test_utils(name="test_utils")
