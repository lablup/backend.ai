# Deviation Report: BA-5075

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Apply RBAC Creator pattern to DomainFairShare | Not implemented | Technical constraint: DomainFairShare is defined as a sub-entity (`"domain:fair_share"` with colon separator) in `RBACElementType` and does not have a corresponding entry in `EntityType`. The current `execute_rbac_entity_creator()` implementation requires `.to_entity_type()` conversion (line 107 in entity_creator.py) to populate the legacy `AssociationScopesEntitiesRow` table, which fails for sub-entities. Implementing RBAC Creator for DomainFairShare would require either: (1) adding DomainFairShare to EntityType (breaks sub-entity semantics), or (2) modifying `execute_rbac_entity_creator()` to skip EntityType conversion for sub-entities (requires framework enhancement beyond scope of this task). DomainFairShare continues to use regular `Creator` pattern. |
| Add DOMAIN_FAIR_SHARE to RBACElementType enum | Alternative applied | Removed duplicate enum entry. The existing `DOMAIN_FAIR_SHARE = "domain:fair_share"` definition (line 127) is used instead of adding a new auto-only entity entry. |
| Add DOMAIN_FAIR_SHARE to scope_entity_combinations | Completed | Successfully added `RBACElementType.DOMAIN_FAIR_SHARE` to `VALID_SCOPE_ENTITY_COMBINATIONS[RBACElementType.RESOURCE_GROUP]`. |
