# Deviation Report: BA-4987

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| VFolderInvitationState import location | Alternative applied | Imported from `ai.backend.manager.data.vfolder.types` instead of `ai.backend.common.dto.manager.vfolder` (the enum is not exposed in common DTOs) |
| Hardcoded invitee email "other-user@test.local" | Alternative applied | Use `regular_user_fixture.email` to ensure user exists in DB for invitation tests |
| SDK rename/delete return types | Test expectation adjusted | Some SDK v2 methods return 204 No Content instead of JSON; tests need to handle this appropriately |
