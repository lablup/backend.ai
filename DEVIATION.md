# Deviation Report: BA-5006

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Create duplicate registry (same name+project) → appropriate error | Not implemented | The `container_registries` table has no unique constraint on `(registry_name, project)`, so duplicate registries are currently allowed by the DB schema. There is also no service-layer guard. Adding a unique constraint or duplicate-check is a schema change beyond the scope of this test-coverage story. |
