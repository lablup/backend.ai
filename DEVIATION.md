# Deviation Report: BA-4990

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Alias list returns all set aliases for an image | Not implemented | No REST endpoint or client method exists for listing image aliases. The `search_aliases` service action exists internally but is not exposed via the REST API (`/admin/images/` routes). The dealias test (S-15) indirectly verifies alias existence by confirming re-dealias fails after removal. |
