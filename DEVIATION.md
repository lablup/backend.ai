# Deviation Report: BA-4981

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Role creation with initial object permissions test | Not implemented | The HTTP API (`CreateRoleRequest` DTO) does not expose an `object_permissions` field. While the service/repository layers support `ObjectPermissionCreateInputBeforeRoleCreation` via `CreateRoleAction`, the REST handler does not pass object permissions through. A component test (which exercises the HTTP layer) cannot test this path without first extending the API. |
