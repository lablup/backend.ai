python_tests(
    dependencies=[
        # The role_preset kind scans the entity package at run time, and
        # `ensure_all_tables_registered` imports every model by name; dependency inference
        # sees neither.
        "src/ai/backend/common:src",
        "src/ai/backend/manager:src",
    ],
)

python_test_utils(name="test_utils")
