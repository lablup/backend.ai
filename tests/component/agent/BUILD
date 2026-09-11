# Needs pulled docker images (session fixture), not the postgres+etcd+redis set the rest of the tree shares.
__defaults__({python_tests: dict(batch_compatibility_tag="component-agent")})

python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
)
