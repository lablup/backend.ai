python_test_utils(
    sources=[
        "conftest.py",
        "model_factory.py",
    ],
    dependencies=[
        ":fixtures",
        "src/ai/backend/manager/api:src",  # indirectly referred via create_app_and_client() fixture
        "src/ai/backend/manager/scheduler:src",  # entrypoint-based import
        "src/ai/backend/manager/plugin:src",  # entrypoint-based import
        "//:reqs#aiosqlite",  # not auto-inferred
    ],
)

python_tests(name="tests")

files(
    name="fixtures",
    sources=["fixtures/*"],
)
