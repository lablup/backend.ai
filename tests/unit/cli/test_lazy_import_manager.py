# def test_lazy_import_manager_cli():
#     # The CLI commands and the `server` module should use lazy imports of their internal dependencies,
#     # to reduce the startup time and avoid unnecessary indirect imports of 3rd-party dependencies.
#     # (See lablup/backend.ai#663, lablup/backend.ai#5327)
#     load_entry_points(allowlist={"ai.backend.manager"})
#     assert not check_module_loaded("ai/backend/manager/api/admin"), (
#         "ai.backend.manager.api.admin should not be loaded when importing ai.backend.manager.cli"
#     )
#     assert not check_module_loaded("ai/backend/manager/models"), (
#         "ai.backend.manager.models should not be loaded when importing ai.backend.manager.cli"
#     )
#     assert not check_module_loaded("ai/backend/manager/actions"), (
#         "ai.backend.manager.actions should not be loaded when importing ai.backend.manager.cli"
#     )
#     assert not check_module_loaded("ai/backend/manager/repositories"), (
#         "ai.backend.manager.repositories should not be loaded when importing ai.backend.manager.cli"
#     )
#     assert not check_module_loaded("ai/backend/manager/services"), (
#         "ai.backend.manager.services should not be loaded when importing ai.backend.manager.cli"
#     )
#     assert not check_module_loaded("ai/backend/manager/sweeper"), (
#         "ai.backend.manager.sweeper should not be loaded when importing ai.backend.manager.cli"
#     )
