python_test_utils()

python_tests(
    name="tests",
    # The seeded-uuid test reads the fixture as data rather than importing it,
    # so the dependency cannot be inferred.
    dependencies=["fixtures/manager:json"],
)
