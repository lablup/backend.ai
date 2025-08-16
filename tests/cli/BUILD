python_test_utils(name="testutils", sources=["helper.py"])

# Split the module import tests into separate test modules
python_test(
    name="test_lazy_import_manager",
    source="test_lazy_import_manager.py",
    dependencies=[
        "src/ai/backend/manager:src",
    ],
)
python_test(
    name="test_lazy_import_agent",
    source="test_lazy_import_agent.py",
    dependencies=[
        "src/ai/backend/agent:src",
    ],
)
python_test(
    name="test_lazy_import_storage_proxy",
    source="test_lazy_import_storage_proxy.py",
    dependencies=[
        "src/ai/backend/storage:src",
    ],
)
