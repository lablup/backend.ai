# Deviation Report: BA-4991

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Image modification tests | Not implemented | REST API v2 does not have modify endpoint yet. Only available in GraphQL legacy API (requires SUPERADMIN). Cannot test via v2 SDK. |
| Image preload tests | Not implemented | REST API v2 does not have preload endpoint. GraphQL legacy API has it but returns "Not implemented" with ok=False. Cannot test via v2 SDK. |
| Image unload tests | Not implemented | REST API v2 does not have unload endpoint. GraphQL legacy API has it but returns "Not implemented" with ok=False. Cannot test via v2 SDK. |

## Notes
- The test file will focus on `forget` and `purge` operations which are fully implemented in REST API v2
- Success criteria related to modification, preload, and unload cannot be verified until REST API v2 endpoints are implemented
- GraphQL legacy API endpoints exist but require different test infrastructure (not using v2 SDK)
