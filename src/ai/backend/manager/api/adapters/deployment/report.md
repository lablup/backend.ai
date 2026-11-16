## deployment

[background](/src/ai/backend/manager/api/adapters/deployment/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/deployment/adapter.py)

Scenario: incomplete 12 / 47

- built from ops (22)
  - admin_search: representative success ✓ · representative rejection ✓
  - admin_search_replicas: representative success ✓ · representative rejection ✓
  - admin_search_revisions: representative success ✓ · representative rejection ✓
  - batch_load_access_tokens_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_auto_scaling_rules_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_policies_by_endpoint_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_policies_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_replicas_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_revisions_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - batch_load_routes_by_ids: representative success ✓ · representative rejection ✓
  - get_access_token: representative success ✓ · representative rejection ✓
  - get_replica: representative success ✓ · representative rejection ✓
  - get_revision: representative success ✓ · representative rejection ✓
  - project_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - search_access_tokens: representative success ✓ · representative rejection ✓
  - search_policies: representative success ✓ · representative rejection ✓
  - search_replicas: representative success ✓ · representative rejection ✓
  - search_revisions: representative success ✓ · representative rejection ✓
  - search_routes: representative success ✓ · representative rejection ✓
  - search_rules: representative success ✓ · representative rejection ✓
- ops + direct implementation (1)
  - get_current_revision: success absent · rejection present 1 (get_ops, single_entity): SCENARIO-GAP
- direct implementation (24)
  - activate_revision: success absent · rejection absent (single_entity): SCENARIO-GAP
  - add_revision: success present 4 · rejection present 7 (single_entity)
  - admin_refresh_deployment_revisions: success absent · rejection absent (global_scope): SCENARIO-GAP
  - bulk_delete_access_tokens: success present 2 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - bulk_delete_rules: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - create: success present 3 · rejection present 2 (scope)
  - create_access_token: success absent · rejection present 1 (single_entity): SCENARIO-GAP
  - create_rule: success present 1 · rejection present 1 (single_entity)
  - delete: success present 2 · rejection present 2 (single_entity)
  - get: success present 2 · rejection present 3 (single_entity)
  - get_policy: success present 1 · rejection present 1 (single_entity)
  - get_rule: success present 1 · rejection present 1 (single_entity)
  - partial_bulk_purge_access_tokens: success present 2 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_purge_rules: success present 3 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_update_rules: success present 2 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - purge_access_token: success present 1 · rejection present 1 (single_field)
  - purge_rule: success present 1 · rejection present 1 (single_entity)
  - replace_options: success present 4 · rejection present 3 (single_entity)
  - search_revision_resource_slots: success present 1 · rejection present 1 (single_field)
  - sync_replicas: success present 1 · rejection present 1 (single_entity)
  - update: success present 5 · rejection present 2 (single_entity)
  - update_route_traffic: success present 1 · rejection present 1 (single_field)
  - update_rule: success present 1 · rejection present 1 (single_entity)
  - upsert_policy: success present 1 · rejection present 1 (single_entity)

**admin_search**

| scenario | verdict |
|---|---|
| [when three deployments exist and a superadmin searches everything without a filter, all three are counted](#searching-the-superadmin-counts-every-deployment) | answered |
| [when a user granted deployment read but not a superadmin searches everything, the role rejects it; the role checks this operation, not the permission graph](#searching-a-user-granted-read-may-not-search-every-deployment) | rejected |

**admin_search_replicas**

| scenario | verdict |
|---|---|
| [when the superadmin searches every replica with a filter, the replicas seeded in advance come back. The requesting user of this row is the superadmin because the search is gated by the global role](#searching_replicas_admin-the-superadmin-searches-the-replicas) | answered |
| [when a user granted nothing tries to search every replica, the search is rejected because the user lacks the global role](#searching_replicas_admin-a-user-granted-nothing-searches-no-replica) | rejected |

**admin_search_revisions**

| scenario | verdict |
|---|---|
| [when revisions are split across deployments in two projects and a superadmin searches everything without a filter, the revisions of both are counted; the role checks this operation](#searching_revisions-the-superadmin-counts-every-revision) | answered |
| [when a user granted read on every deployment but not a superadmin searches every revision, the role rejects it](#searching_revisions-a-user-granted-read-may-not-search-every-revision) | rejected |

**batch_load_access_tokens_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read batch loads the access tokens the deployment holds by id, those tokens come back](#batch_loading_access_tokens-a-user-granted-deployment-read-loads-the-tokens-by-id) | answered |
| [when a user granted nothing tries to batch load the access tokens the deployment holds by id, every entry is rejected because the user lacks permission](#batch_loading_access_tokens-a-user-granted-nothing-gets-a-refusal-for-each-token) | rejected |

**batch_load_auto_scaling_rules_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read batch loads the auto-scaling rules the deployment holds by id, those rules come back](#batch_loading_rules-a-user-granted-deployment-read-loads-the-rules-by-id) | answered |
| [when a user granted nothing tries to batch load the auto-scaling rules the deployment holds by id, every entry is rejected because the user lacks permission](#batch_loading_rules-a-user-granted-nothing-gets-a-refusal-for-each-rule) | rejected |

**batch_load_policies_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read batch loads the policy the deployment holds by id, that policy comes back](#batch_loading_policies-a-user-granted-deployment-read-loads-the-policy-by-id) | answered |
| [when a user granted nothing tries to batch load the policy the deployment holds by id, every entry is rejected because the user lacks permission](#batch_loading_policies-a-user-granted-nothing-gets-a-refusal-for-the-policy) | rejected |

**batch_load_replicas_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read batch loads the replicas the deployment holds by id, those replicas come back](#batch_loading_replicas-a-user-granted-deployment-read-loads-the-replicas-by-id) | answered |
| [when a user granted nothing tries to batch load the replicas the deployment holds by id, every entry is rejected because the user lacks permission](#batch_loading_replicas-a-user-granted-nothing-gets-a-refusal-for-the-replicas) | rejected |

**batch_load_revisions_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read in only one project loads a readable revision, a revision of another project, and an id nothing answers to at once, a revision, a rejection, and an empty entry come back in the order given](#reading_revisions-loading-revisions-by-id-answers-each-id-on-its-own) | answered |

**batch_load_routes_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted deployment read batch loads the routes the deployment holds by id, those routes come back](#batch_loading_routes-a-user-granted-deployment-read-loads-the-routes-by-id) | answered |
| [when a user granted nothing tries to batch load the routes the deployment holds by id, every entry is rejected because the user lacks permission](#batch_loading_routes-a-user-granted-nothing-gets-a-refusal-for-the-routes) | rejected |

**get_access_token**

| scenario | verdict |
|---|---|
| [when a user granted deployment read reads one of the access tokens the deployment holds, that token comes back](#reading_access_tokens-a-user-granted-deployment-read-reads-a-token) | answered |
| [when a user granted nothing tries to read one of the access tokens the deployment holds, the lookup that finds the deployment holding the token is rejected](#reading_access_tokens-a-user-granted-nothing-reads-no-token) | rejected |

**get_replica**

| scenario | verdict |
|---|---|
| [when a user granted deployment read reads a replica of the deployment, that replica comes back](#reading_replicas-a-user-granted-deployment-read-reads-the-replica) | answered |
| [when a user granted nothing tries to read a replica of the deployment, the lookup that finds the deployment holding the replica is rejected](#reading_replicas-a-user-granted-nothing-reads-no-replica) | rejected |

**get_revision**

| scenario | verdict |
|---|---|
| [when a user granted deployment read reads a revision of that deployment by id, that revision comes back](#reading_revisions-a-user-granted-read-reads-a-revision-by-id) | answered |
| [when a superadmin reads a revision by an id nothing answers to, the call is rejected as not found; nothing is hidden from someone who passes every check](#reading_revisions-a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted deployment read reads a revision by an id nothing answers to, the call is rejected for the same reason as an id the user cannot see](#reading_revisions-a-revision-id-nothing-answers-to-is-refused-as-unresolvable) | rejected |
| [when a user with no deployment grant reads a revision by id, the call is rejected because the key cannot be decrypted](#reading_revisions-a-user-granted-nothing-may-not-read-a-revision) | rejected |

**project_search**

| scenario | verdict |
|---|---|
| [when deployments are split across two projects and a user granted read on only one side searches that project, only that project's deployments come back](#searching-searching-a-project-finds-only-its-own-deployments) | answered |
| [when a user without read permission on the project searches the project, the call is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-search-a-project) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when two users each created a deployment in the same project and the one granted read in their own scope searches their own, only what they created comes back](#searching-searching-my-own-finds-only-what-i-made) | answered |
| [when a user not granted read in their own scope searches their own, the call is rejected for lack of permission; here too the permission checks it rather than only narrowing the scope](#searching-a-user-granted-nothing-may-not-search-even-their-own) | rejected |

**search_access_tokens**

| scenario | verdict |
|---|---|
| [when a user granted deployment read searches the access tokens the deployment holds with a filter, those tokens come back](#searching_access_tokens-a-user-granted-deployment-read-searches-the-tokens) | answered |
| [when a user granted nothing tries to search the access tokens the deployment holds, the search is rejected because the user lacks permission](#searching_access_tokens-a-user-granted-nothing-searches-no-token) | rejected |

**search_policies**

| scenario | verdict |
|---|---|
| [when the superadmin searches the deployment policies with a filter, the policy seeded in advance comes back. The requesting user of this row is the superadmin because the search is gated by the global role](#searching_policies-the-superadmin-searches-the-policies) | answered |
| [when a user granted nothing tries to search the deployment policies, the search is rejected because the user lacks the global role](#searching_policies-a-user-granted-nothing-searches-no-policy) | rejected |

**search_replicas**

| scenario | verdict |
|---|---|
| [when a user granted deployment read searches the replica of a route with traffic enabled, the replicas seeded in advance come back](#searching_replicas-a-user-granted-deployment-read-searches-the-replica-with-traffic-enabled) | answered |
| [when a user granted deployment read searches the replicas of the deployment with a filter, the replicas seeded in advance come back](#searching_replicas-a-user-granted-deployment-read-searches-the-replicas) | answered |
| [when a user granted nothing tries to search the replicas of the deployment, the search is rejected because the user lacks permission](#searching_replicas-a-user-granted-nothing-searches-no-replica) | rejected |

**search_revisions**

| scenario | verdict |
|---|---|
| [when a user granted read on a deployment holding three revisions searches that deployment's revisions, all three are counted](#searching_revisions-a-user-granted-read-counts-every-revision-of-a-deployment) | answered |
| [when revisions are split across deployments in two projects and a user granted read on only one side searches that side's deployment revisions, only that side comes back](#searching_revisions-another-deployments-revisions-stay-out-of-a-deployment-search) | answered |
| [searching the revisions of a deployment holding three revisions filtered by number leaves only the one with that number](#searching_revisions-filtering-revisions-by-number-leaves-only-that-one) | answered |
| [when a user with no deployment grant searches a deployment's revisions, the call is rejected for lack of permission](#searching_revisions-a-user-granted-nothing-may-not-search-a-deployments-revisions) | rejected |

**search_routes**

| scenario | verdict |
|---|---|
| [when a user granted deployment read searches the routes of the deployment with a filter, the routes seeded in advance come back](#searching_routes-a-user-granted-deployment-read-searches-the-routes) | answered |
| [when a user granted nothing tries to search the routes of the deployment, the search is rejected because the user lacks permission](#searching_routes-a-user-granted-nothing-searches-no-route) | rejected |

**search_rules**

| scenario | verdict |
|---|---|
| [when a user granted deployment read searches the auto-scaling rules the deployment holds with a filter, those rules come back](#searching_rules-a-user-granted-deployment-read-searches-the-rules) | answered |
| [when a user granted nothing tries to search the auto-scaling rules the deployment holds, the search is rejected because the user lacks permission](#searching_rules-a-user-granted-nothing-searches-no-rule) | rejected |

**get_current_revision**

| scenario | verdict |
|---|---|
| [reading the current revision of a deployment holding no revision is rejected because there is no current revision](#reading-a-deployment-holding-no-revision-answers-nothing-as-its-current-one) | rejected |

**add_revision**

| scenario | verdict |
|---|---|
| [adding a revision without resources and cluster when there is neither a preset nor a required slot brings back a revision on one node with size 1 and no resource slot](#adding_revisions-a-revision-added-without-resources-runs-on-one-node-with-no-slot) | answered |
| [when a user granted create adds a revision with every setting to a deployment that has no revision, the revision numbered 1 comes back with exactly the settings that were given](#adding_revisions-a-user-granted-create-adds-the-first-revision) | answered |
| [adding a revision to a deployment that holds one revision brings back the revision numbered 2](#adding_revisions-the-next-revision-is-numbered-one-past-the-last) | answered |
| [when a superadmin holding no grant on the deployment or on their own model vfolder adds a revision to another user's deployment, the revision is added; the role passes through both the deployment permission and the vfolder permission](#adding_revisions-the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant) | answered |
| [when a user granted create on the deployment but not read on the model vfolder adds a revision with that vfolder, the call is rejected because the vfolder is not found](#adding_revisions-a-model-folder-the-caller-may-not-read-is-not-found) | rejected |
| [when a user who borrowed another user's model vfolder as read-only adds a revision that mounts it read-write, the call is rejected because it exceeds the vfolder permission](#adding_revisions-a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused) | rejected |
| [when a slot every revision must fill is set and a revision is added without it, the call is rejected because the input is wrong](#adding_revisions-a-revision-missing-a-required-slot-is-refused) | rejected |
| [adding a revision without an image and without a preset is rejected because the input is wrong](#adding_revisions-a-revision-with-no-image-from-any-layer-is-refused) | rejected |
| [adding a revision with a runtime variant that does not read vfolder files, without a model definition and without a preset, is rejected in model definition validation because a model has no name](#adding_revisions-a-revision-with-no-model-definition-from-any-layer-is-refused) | rejected |
| [adding a revision without a runtime variant and without a preset is rejected because the input is wrong](#adding_revisions-a-revision-with-no-runtime-variant-from-any-layer-is-refused) | rejected |
| [when a user granted only read on the deployment adds a revision, the call is rejected for lack of permission](#adding_revisions-a-user-granted-only-read-may-not-add-a-revision) | rejected |

**bulk_delete_access_tokens**

| scenario | verdict |
|---|---|
| [when a user granted deployment purge purges several access tokens the deployment holds at once, the ids of those tokens come back](#retiring_access_tokens-a-user-granted-deployment-purge-purges-tokens-at-once) | answered |
| [when a user granted nothing tries to purge several access tokens the deployment holds at once, nothing is purged and the id list comes back empty](#retiring_access_tokens-a-user-granted-nothing-purges-no-token-at-once) | answered |

**create**

| scenario | verdict |
|---|---|
| [creating a deployment without a name names it after the user who created it](#creating-a-deployment-made-without-a-name-is-named-after-its-maker) | answered |
| [when a user granted create in a project creates a deployment, a deployment that belongs to the project and is owned by the requesting user is created with no revision](#creating-a-user-granted-create-in-a-project-makes-a-deployment-there) | answered |
| [turning entity permission enforcement off lets a user with no grant create a deployment, because the permission graph checks this operation, not the role](#creating-turning-enforcement-off-lets-a-user-create-a-deployment) | answered |
| [creating a deployment in a project other than the one where the create grant was given is rejected for lack of permission](#creating-a-create-grant-in-another-project-does-not-reach-this-one) | rejected |
| [when a user granted no deployment permission creates a deployment, the call is rejected for lack of permission](#creating-a-user-granted-nothing-may-not-create-a-deployment) | rejected |

**create_access_token**

| scenario | verdict |
|---|---|
| [when a user granted deployment create tries to make an access token of the deployment, the create is rejected because the deployment's scaling group has no proxy target configured](#creating_access_tokens-a-user-granted-deployment-create-makes-no-token) | rejected |

**create_rule**

| scenario | verdict |
|---|---|
| [when a user granted deployment create makes an auto-scaling rule of the deployment, the rule made comes back](#creating_rules-a-user-granted-deployment-create-makes-a-rule) | answered |
| [when a user granted nothing tries to make an auto-scaling rule of the deployment, the create is rejected because the user lacks permission](#creating_rules-a-user-granted-nothing-makes-no-rule) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when a user granted soft-delete deletes a deployment, the response says the deployment's deletion has started](#retiring-a-user-granted-soft-delete-retires-a-deployment) | answered |
| [when a superadmin holding no grant deletes another user's deployment, the response says the deployment's deletion has started; the role passes through the permission graph](#retiring-the-superadmin-retires-anothers-deployment-without-a-grant) | answered |
| [when a user granted only update and not soft-delete deletes a deployment, the call is rejected for lack of permission; deletion is a different operation from update](#retiring-a-user-granted-only-update-may-not-retire-a-deployment) | rejected |
| [when a superadmin deletes an id nothing answers to, the call is rejected as not found](#retiring-retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a deployment exists and a user granted read reads it by id, that deployment comes back in the response](#reading-a-user-granted-read-reads-a-deployment-by-id) | answered |
| [when a superadmin holding no grant reads another user's deployment by id, that deployment comes back in the response; the role passes through the permission graph](#reading-the-superadmin-reads-anothers-deployment-without-a-grant) | answered |
| [when the same deployment exists and a user with no grant reads it, the call is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-a-deployment) | rejected |
| [when a superadmin reads by an id nothing answers to, the call is rejected as not found; only someone who passes the permission check sees this response](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted read reads by an id nothing answers to, the call is rejected for lack of permission rather than as not found, because no permission is held on a row that does not exist](#reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user) | rejected |

**get_policy**

| scenario | verdict |
|---|---|
| [when a user granted deployment read reads the policy the deployment holds, that policy comes back](#reading_policy-a-user-granted-deployment-read-reads-the-policy) | answered |
| [when a user granted nothing tries to read the policy the deployment holds, the read is rejected because the user lacks permission](#reading_policy-a-user-granted-nothing-reads-no-policy) | rejected |

**get_rule**

| scenario | verdict |
|---|---|
| [when a user granted deployment read reads one of the rules seeded in advance by id, that rule comes back](#reading_rules-a-user-granted-deployment-read-reads-a-rule) | answered |
| [when a user granted nothing tries to read one of the rules seeded in advance by id, the lookup that finds the deployment holding the rule is rejected](#reading_rules-a-user-granted-nothing-reads-no-rule) | rejected |

**partial_bulk_purge_access_tokens**

| scenario | verdict |
|---|---|
| [when a user with no grant tries to purge several deployment tokens at once, nothing is purged and every token comes back in the failed list because the user lacks permission](#partial_bulk_access_tokens-a-user-granted-nothing-purges-none-of-several-tokens) | answered |
| [when a user granted deployment purge purges two deployment tokens and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_access_tokens-purging-several-tokens-answers-for-the-missing-one) | answered |

**partial_bulk_purge_rules**

| scenario | verdict |
|---|---|
| [when a user granted only deployment update tries to purge several auto-scaling rules at once, nothing is purged and every rule comes back in the failed list because the user lacks permission](#partial_bulk_auto_scaling_rules-a-deployment-editor-purges-none-of-several-rules) | answered |
| [when a user with no grant tries to purge several auto-scaling rules at once, nothing is purged and every rule comes back in the failed list because the user lacks permission](#partial_bulk_auto_scaling_rules-a-user-granted-nothing-purges-none-of-several-rules) | answered |
| [when a user granted deployment purge purges two auto-scaling rules and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_auto_scaling_rules-purging-several-rules-answers-for-the-missing-one) | answered |

**partial_bulk_update_rules**

| scenario | verdict |
|---|---|
| [when a user granted deployment update changes the metric name of several auto-scaling rules at once, every rule comes back with the new name and nothing failed](#partial_bulk_auto_scaling_rules-a-deployment-editor-edits-several-rules-at-once) | answered |
| [when a user with no grant tries to update several auto-scaling rules at once, nothing is updated and every rule comes back in the failed list because the user lacks permission](#partial_bulk_auto_scaling_rules-a-user-granted-nothing-edits-none-of-several-rules) | answered |

**purge_access_token**

| scenario | verdict |
|---|---|
| [when a user granted deployment read and purge purges one of the access tokens the deployment holds, the id of that token comes back. The purge reads the deployment first, so read is also required](#retiring_access_tokens-a-user-granted-deployment-purge-purges-a-token) | answered |
| [when a user granted nothing tries to purge one of the access tokens the deployment holds, the lookup that finds the deployment holding the token is rejected](#retiring_access_tokens-a-user-granted-nothing-purges-no-token) | rejected |

**purge_rule**

| scenario | verdict |
|---|---|
| [when a user granted deployment read and purge purges one of the auto-scaling rules the deployment holds, the id of that rule comes back. The purge reads the deployment first, so read is also required](#retiring_rules-a-user-granted-deployment-purge-purges-a-rule) | answered |
| [when a user granted nothing tries to purge one of the auto-scaling rules the deployment holds, the lookup that finds the deployment holding the rule is rejected](#retiring_rules-a-user-granted-nothing-purges-no-rule) | rejected |

**replace_options**

| scenario | verdict |
|---|---|
| [when a user granted update replaces the options with the defaults and per-handler settings, what was given becomes the new options as a whole and the response carries only those options](#options-a-user-granted-update-replaces-the-options-whole) | answered |
| [replacing the options with the selection policy STRICT keeps that policy on the new options](#options-replacing-with-a-strict-policy-keeps-it-strict) | answered |
| [replacing the options of a deployment that holds inherited per-handler settings with only the defaults leaves none of the inherited settings](#options-replacing-with-no-handler-entry-drops-the-inherited-ones) | answered |
| [replacing the options of a deployment whose selection policy is STRICT without a policy keeps it STRICT](#options-replacing-without-a-policy-keeps-the-stored-one) | answered |
| [when a user granted only read replaces the options, the call is rejected for lack of permission](#options-a-user-granted-only-read-may-not-replace-the-options) | rejected |
| [replacing the options with the same handler name twice is rejected because the input is wrong](#options-naming-a-handler-twice-is-refused) | rejected |
| [replacing the options with an unregistered handler name is rejected because the input is wrong](#options-naming-an-unregistered-handler-is-refused) | rejected |

**search_revision_resource_slots**

| scenario | verdict |
|---|---|
| [when a user granted read on a deployment holding a revision that allocates two slots searches that revision's slots, both are counted](#searching_revisions-a-user-granted-read-counts-every-slot-a-revision-allocates) | answered |
| [when a user with no deployment grant searches a deployment revision's slots, the call is rejected with a response that the revision is not found](#searching_revisions-a-user-granted-nothing-may-not-search-a-revisions-slots) | rejected |

**sync_replicas**

| scenario | verdict |
|---|---|
| [when a user granted update asks to sync the replicas, the response says syncing has started](#syncing-a-user-granted-update-starts-syncing-the-replicas) | answered |
| [when a user granted only read asks to sync the replicas, the call is rejected for lack of permission](#syncing-a-user-granted-only-read-may-not-sync-the-replicas) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted update changes a deployment that is not public to public, the state comes back changed to public](#editing-a-user-granted-update-opens-a-deployment-to-the-public) | answered |
| [when a user granted update raises the replica count, the intended replica count becomes the new value](#editing-a-user-granted-update-raises-the-replica-count) | answered |
| [when a user granted update changes the name, only the name becomes the new value and everything else stays the same](#editing-a-user-granted-update-renames-a-deployment) | answered |
| [clearing the tags of a deployment that holds tags leaves no tag](#editing-clearing-the-tags-of-a-deployment-leaves-none) | answered |
| [when a superadmin holding no grant changes the name of a deployment another user created, only the name becomes the new value; the role passes through the permission graph](#editing-the-superadmin-renames-anothers-deployment-without-a-grant) | answered |
| [when a user granted only read updates a deployment, the call is rejected for lack of permission](#editing-a-user-granted-only-read-may-not-update-a-deployment) | rejected |
| [when a superadmin updates an id nothing answers to, the call is rejected as not found](#editing-updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**update_route_traffic**

| scenario | verdict |
|---|---|
| [when a user granted deployment read and update turns the traffic of a route on, the route with its traffic turned on comes back. The traffic change reads the deployment first, so read is also required](#editing_route_traffic-a-user-granted-deployment-update-opens-the-traffic) | answered |
| [when a user granted nothing tries to turn the traffic of a route, the lookup that finds the deployment holding the route is rejected](#editing_route_traffic-a-user-granted-nothing-changes-no-traffic) | rejected |

**update_rule**

| scenario | verdict |
|---|---|
| [when a user granted deployment read and update edits one of the rules seeded in advance, the rule edited comes back. The edit reads the deployment first, so read is also required](#updating_rules-a-user-granted-deployment-update-edits-a-rule) | answered |
| [when a user granted nothing tries to edit one of the rules seeded in advance, the lookup that finds the deployment holding the rule is rejected](#updating_rules-a-user-granted-nothing-edits-no-rule) | rejected |

**upsert_policy**

| scenario | verdict |
|---|---|
| [when a user granted deployment update puts a policy on the deployment, the policy put comes back. The upsert replaces an existing policy, so the call is gated by update](#upserting_policy-a-user-granted-deployment-update-puts-the-policy) | answered |
| [when a user granted nothing tries to put a policy on the deployment, the upsert is rejected because the user lacks permission](#upserting_policy-a-user-granted-nothing-puts-no-policy) | rejected |

### admin_search

<a id="searching-the-superadmin-counts-every-deployment"></a>

#### [the-superadmin-counts-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when three deployments exist and a superadmin searches everything without a filter, all three are counted

Given

- 3 deployments in the same project and one user of that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-2: replica count 1, has no revision yet

When

- DeploymentAdapter.admin_search: user-1 searches everything without a filter

Then

- every deployment seeded in advance is counted, and nothing else
  - items = ['other-1', 'other-2', 'wanted-1']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-read-may-not-search-every-deployment"></a>

#### [a-user-granted-read-may-not-search-every-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when a user granted deployment read but not a superadmin searches everything, the role rejects it; the role checks this operation, not the permission graph

Given

- 3 deployments in the same project and one user of that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-2: replica count 1, has no revision yet

When

- DeploymentAdapter.admin_search: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_replicas

<a id="searching_replicas_admin-the-superadmin-searches-the-replicas"></a>

#### [the-superadmin-searches-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_searching_replicas_admin.py): pass

when the superadmin searches every replica with a filter, the replicas seeded in advance come back. The requesting user of this row is the superadmin because the search is gated by the global role

Given

- one deployment holding one revision and 1 replica routes, and the superadmin, one more replica route with traffic enabled
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - superadmin user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.admin_search_replicas: user-1 searches every replica with one filter, one order and pagination

Then

- the replica the filter excludes does not come back, and the replicas seeded in advance come back with their count
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the route seeded in advance
  - items[0].field_id: same as the id of the route seeded in advance
  - items[0].deployment_id: same as the id of the deployment the replica serves
  - items[0].revision_id: same as the id of the revision seeded in advance
  - items[0].session_id = None
  - items[0].readiness_status = 'NOT_CHECKED'
  - items[0].liveness_status = 'NOT_CHECKED'
  - items[0].activeness_status = 'INACTIVE'
  - items[0].status = 'provisioning'
  - items[0].traffic_status = 'inactive'
  - items[0].health_status = 'not_checked'
  - items[0].created_at: the time this run wrote

<a id="searching_replicas_admin-a-user-granted-nothing-searches-no-replica"></a>

#### [a-user-granted-nothing-searches-no-replica](/tests/scenario/bai_scenario/manager/deployment/test_searching_replicas_admin.py): pass

when a user granted nothing tries to search every replica, the search is rejected because the user lacks the global role

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.admin_search_replicas: user-1 searches every replica with one filter, one order and pagination

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_revisions

<a id="searching_revisions-the-superadmin-counts-every-revision"></a>

#### [the-superadmin-counts-every-revision](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when revisions are split across deployments in two projects and a superadmin searches everything without a filter, the revisions of both are counted; the role checks this operation

Given

- revisions are split between deployments in two projects, 2 and 1, and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Project other-1
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment elsewhere-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - superadmin user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment wanted-1: has one revision
  - Deployment wanted-1: has one revision
  - Deployment elsewhere-1: has one revision

When

- DeploymentAdapter.admin_search_revisions: user-1 searches every revision without a filter

Then

- every revision seeded in advance is counted, and nothing else
  - items.id: same as the revisions counted
  - items.revision_number = [1, 1, 2]
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-read-may-not-search-every-revision"></a>

#### [a-user-granted-read-may-not-search-every-revision](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when a user granted read on every deployment but not a superadmin searches every revision, the role rejects it

Given

- one deployment holding 1 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.admin_search_revisions: user-1 searches every revision without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_access_tokens_by_ids

<a id="batch_loading_access_tokens-a-user-granted-deployment-read-loads-the-tokens-by-id"></a>

#### [a-user-granted-deployment-read-loads-the-tokens-by-id](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_access_tokens.py): pass

when a user granted deployment read batch loads the access tokens the deployment holds by id, those tokens come back

Given

- one deployment holding 2 access tokens, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.batch_load_access_tokens_by_ids: user-1 batch loads 2 tokens by id

Then

- the tokens come back in the order they were put in the request
  - loaded count = 2
  - [0].id: same as the id of the token seeded in advance
  - [0].field_id: same as the id of the token seeded in advance
  - [0].token = 'scenario-token'
  - [0].expires_at = None
  - [0].created_at: the time this run wrote
  - [1].id: same as the id of the token seeded in advance
  - [1].field_id: same as the id of the token seeded in advance
  - [1].token = 'scenario-token'
  - [1].expires_at = None
  - [1].created_at: the time this run wrote

<a id="batch_loading_access_tokens-a-user-granted-nothing-gets-a-refusal-for-each-token"></a>

#### [a-user-granted-nothing-gets-a-refusal-for-each-token](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_access_tokens.py): pass

when a user granted nothing tries to batch load the access tokens the deployment holds by id, every entry is rejected because the user lacks permission

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.batch_load_access_tokens_by_ids: user-1 batch loads 2 tokens by id

Then

- no token comes back and every entry is the exception the check raised
  - loaded count = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_auto_scaling_rules_by_ids

<a id="batch_loading_rules-a-user-granted-deployment-read-loads-the-rules-by-id"></a>

#### [a-user-granted-deployment-read-loads-the-rules-by-id](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_rules.py): pass

when a user granted deployment read batch loads the auto-scaling rules the deployment holds by id, those rules come back

Given

- one deployment holding 2 auto-scaling rules, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.batch_load_auto_scaling_rules_by_ids: user-1 batch loads 2 rules by id

Then

- the rules come back in the order they were put in the request
  - loaded count = 2
  - [0].id: same as the id of the rule seeded in advance
  - [0].field_id: same as the id of the rule seeded in advance
  - [0].deployment_id: same as the id of the deployment the rule scales
  - [0].metric_source = 'KERNEL'
  - [0].metric_name = 'cpu_util'
  - [0].min_threshold = None
  - [0].max_threshold = None
  - [0].step_size = 1
  - [0].time_window = 60
  - [0].min_replicas = None
  - [0].max_replicas = None
  - [0].prometheus_query_preset_id = None
  - [0].created_at: the time this run wrote
  - [0].last_triggered_at = None
  - [1].id: same as the id of the rule seeded in advance
  - [1].field_id: same as the id of the rule seeded in advance
  - [1].deployment_id: same as the id of the deployment the rule scales
  - [1].metric_source = 'KERNEL'
  - [1].metric_name = 'cpu_util'
  - [1].min_threshold = None
  - [1].max_threshold = None
  - [1].step_size = 1
  - [1].time_window = 60
  - [1].min_replicas = None
  - [1].max_replicas = None
  - [1].prometheus_query_preset_id = None
  - [1].created_at: the time this run wrote
  - [1].last_triggered_at = None

<a id="batch_loading_rules-a-user-granted-nothing-gets-a-refusal-for-each-rule"></a>

#### [a-user-granted-nothing-gets-a-refusal-for-each-rule](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_rules.py): pass

when a user granted nothing tries to batch load the auto-scaling rules the deployment holds by id, every entry is rejected because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.batch_load_auto_scaling_rules_by_ids: user-1 batch loads 2 rules by id

Then

- no rule comes back and every entry is the exception the check raised
  - loaded count = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_policies_by_ids

<a id="batch_loading_policies-a-user-granted-deployment-read-loads-the-policy-by-id"></a>

#### [a-user-granted-deployment-read-loads-the-policy-by-id](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_policies.py): pass

when a user granted deployment read batch loads the policy the deployment holds by id, that policy comes back

Given

- one deployment holding one policy, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy

When

- DeploymentAdapter.batch_load_policies_by_ids: user-1 batch loads the policy seeded in advance by id

Then

- the policy comes back in the order it was put in the request
  - [0].id: same as the id of the policy seeded in advance
  - [0].field_id: same as the id of the policy seeded in advance
  - [0].deployment_id: same as the id of the deployment the policy sets
  - [0].strategy_spec.strategy: same as the strategy of the policy seeded in advance
  - [0].strategy_spec.max_surge = IntOrPercent(count=1, percent=None)
  - [0].strategy_spec.max_unavailable = IntOrPercent(count=0, percent=None)
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading_policies-a-user-granted-nothing-gets-a-refusal-for-the-policy"></a>

#### [a-user-granted-nothing-gets-a-refusal-for-the-policy](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_policies.py): pass

when a user granted nothing tries to batch load the policy the deployment holds by id, every entry is rejected because the user lacks permission

Given

- one deployment holding one policy, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy

When

- DeploymentAdapter.batch_load_policies_by_ids: user-1 batch loads the policy seeded in advance by id

Then

- no policy comes back and every entry is the exception the check raised
  - rejected: NotEnoughPermission

### batch_load_replicas_by_ids

<a id="batch_loading_replicas-a-user-granted-deployment-read-loads-the-replicas-by-id"></a>

#### [a-user-granted-deployment-read-loads-the-replicas-by-id](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_replicas.py): pass

when a user granted deployment read batch loads the replicas the deployment holds by id, those replicas come back

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.batch_load_replicas_by_ids: user-1 batch loads the replicas seeded in advance by id

Then

- the replicas come back in the order they were put in the request
  - [0].id: same as the id of the route seeded in advance
  - [0].field_id: same as the id of the route seeded in advance
  - [0].deployment_id: same as the id of the deployment the replica serves
  - [0].revision_id: same as the id of the revision seeded in advance
  - [0].session_id = None
  - [0].readiness_status = 'NOT_CHECKED'
  - [0].liveness_status = 'NOT_CHECKED'
  - [0].activeness_status = 'INACTIVE'
  - [0].status = 'provisioning'
  - [0].traffic_status = 'inactive'
  - [0].health_status = 'not_checked'
  - [0].created_at: the time this run wrote

<a id="batch_loading_replicas-a-user-granted-nothing-gets-a-refusal-for-the-replicas"></a>

#### [a-user-granted-nothing-gets-a-refusal-for-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_replicas.py): pass

when a user granted nothing tries to batch load the replicas the deployment holds by id, every entry is rejected because the user lacks permission

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.batch_load_replicas_by_ids: user-1 batch loads the replicas seeded in advance by id

Then

- no replica comes back and every entry is the exception the check raised
  - rejected: NotEnoughPermission

### batch_load_revisions_by_ids

<a id="reading_revisions-loading-revisions-by-id-answers-each-id-on-its-own"></a>

#### [loading-revisions-by-id-answers-each-id-on-its-own](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

when a user granted deployment read in only one project loads a readable revision, a revision of another project, and an id nothing answers to at once, a revision, a rejection, and an empty entry come back in the order given

Given

- revisions are split between deployments in two projects, 1 and 1, and one user granted READ on deployments in one project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Project other-1
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment elsewhere-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment wanted-1: has one revision
  - Deployment elsewhere-1: has one revision

When

- DeploymentAdapter.batch_load_revisions_by_ids: user-1 loads the revision of wanted-1, the revision of a deployment in another project, and an id nothing answers to, in that order, in one call

Then

- a revision, a rejection and an empty place come back in the order given
  - len = 3
  - [0].id: same as the revision seeded in advance
  - [0].deployment_id: same as the deployment seeded in advance
  - [0].revision_number = 1
  - [0].image_id: same as the image seeded in advance
  - [0].cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - [0].resource_config.resource_group_name = 'resource-group-1'
  - [0].resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - [0].resource_config.resource_opts = None
  - [0].model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - [0].model_runtime_config.inference_runtime_config = None
  - [0].model_runtime_config.environ = None
  - [0].model_runtime_config.runtime_variant_preset_values = []
  - [0].model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - [0].model_mount_config.mount_destination = '/models'
  - [0].model_mount_config.definition_path = ''
  - [0].model_mount_config.subpath = None
  - [0].model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - [0].created_at: the time this run wrote
  - [0].extra_mounts = []
  - [0].revision_preset_id = None
  - [1] = 'NotEnoughPermission'
  - [2] = None

### batch_load_routes_by_ids

<a id="batch_loading_routes-a-user-granted-deployment-read-loads-the-routes-by-id"></a>

#### [a-user-granted-deployment-read-loads-the-routes-by-id](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_routes.py): pass

when a user granted deployment read batch loads the routes the deployment holds by id, those routes come back

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.batch_load_routes_by_ids: user-1 batch loads the routes seeded in advance by id

Then

- the routes come back in the order they were put in the request
  - [0].id: same as the id of the route seeded in advance
  - [0].field_id: same as the id of the route seeded in advance
  - [0].deployment_id: same as the id of the deployment the route serves
  - [0].session_id = None
  - [0].status = 'provisioning'
  - [0].health_status = 'not_checked'
  - [0].traffic_ratio = 1.0
  - [0].created_at: the time this run wrote
  - [0].revision_id: same as the id of the revision seeded in advance
  - [0].traffic_status = 'inactive'
  - [0].error_data = {}

<a id="batch_loading_routes-a-user-granted-nothing-gets-a-refusal-for-the-routes"></a>

#### [a-user-granted-nothing-gets-a-refusal-for-the-routes](/tests/scenario/bai_scenario/manager/deployment/test_batch_loading_routes.py): pass

when a user granted nothing tries to batch load the routes the deployment holds by id, every entry is rejected because the user lacks permission

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.batch_load_routes_by_ids: user-1 batch loads the routes seeded in advance by id

Then

- no route comes back and every entry is the exception the check raised
  - rejected: NotEnoughPermission

### get_access_token

<a id="reading_access_tokens-a-user-granted-deployment-read-reads-a-token"></a>

#### [a-user-granted-deployment-read-reads-a-token](/tests/scenario/bai_scenario/manager/deployment/test_reading_access_tokens.py): pass

when a user granted deployment read reads one of the access tokens the deployment holds, that token comes back

Given

- one deployment holding 2 access tokens, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.get_access_token: user-1 reads one of the tokens seeded in advance

Then

- the token read comes back
  - id: same as the id of the token seeded in advance
  - field_id: same as the id of the token seeded in advance
  - token = 'scenario-token'
  - expires_at = None
  - created_at: the time this run wrote

<a id="reading_access_tokens-a-user-granted-nothing-reads-no-token"></a>

#### [a-user-granted-nothing-reads-no-token](/tests/scenario/bai_scenario/manager/deployment/test_reading_access_tokens.py): pass

when a user granted nothing tries to read one of the access tokens the deployment holds, the lookup that finds the deployment holding the token is rejected

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.get_access_token: user-1 reads one of the tokens seeded in advance

Then

- the call is rejected
  - rejected: GenericBadRequest

### get_replica

<a id="reading_replicas-a-user-granted-deployment-read-reads-the-replica"></a>

#### [a-user-granted-deployment-read-reads-the-replica](/tests/scenario/bai_scenario/manager/deployment/test_reading_replicas.py): pass

when a user granted deployment read reads a replica of the deployment, that replica comes back

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.get_replica: user-1 reads one replica seeded in advance

Then

- the replica seeded in advance comes back whole
  - id: same as the id of the route seeded in advance
  - field_id: same as the id of the route seeded in advance
  - deployment_id: same as the id of the deployment the replica serves
  - revision_id: same as the id of the revision seeded in advance
  - session_id = None
  - readiness_status = 'NOT_CHECKED'
  - liveness_status = 'NOT_CHECKED'
  - activeness_status = 'INACTIVE'
  - status = 'provisioning'
  - traffic_status = 'inactive'
  - health_status = 'not_checked'
  - created_at: the time this run wrote

<a id="reading_replicas-a-user-granted-nothing-reads-no-replica"></a>

#### [a-user-granted-nothing-reads-no-replica](/tests/scenario/bai_scenario/manager/deployment/test_reading_replicas.py): pass

when a user granted nothing tries to read a replica of the deployment, the lookup that finds the deployment holding the replica is rejected

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.get_replica: user-1 reads one replica seeded in advance

Then

- the call is rejected
  - rejected: GenericBadRequest

### get_revision

<a id="reading_revisions-a-user-granted-read-reads-a-revision-by-id"></a>

#### [a-user-granted-read-reads-a-revision-by-id](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

when a user granted deployment read reads a revision of that deployment by id, that revision comes back

Given

- one deployment holding 1 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.get_revision: user-1 reads a revision by the id of the first revision of deployment-1

Then

- the whole revision comes back
  - id: same as the revision seeded in advance
  - deployment_id: same as the deployment seeded in advance
  - revision_number = 1
  - image_id: same as the image seeded in advance
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: the time this run wrote
  - extra_mounts = []
  - revision_preset_id = None

<a id="reading_revisions-a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [a-revision-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

when a superadmin reads a revision by an id nothing answers to, the call is rejected as not found; nothing is hidden from someone who passes every check

Given

- one deployment holding 1 revisions and a user with no deployment permission who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - superadmin user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.get_revision: user-1 reads a revision by an id nothing answers to

Then

- the call is rejected
  - rejected: FieldNotFoundError

<a id="reading_revisions-a-revision-id-nothing-answers-to-is-refused-as-unresolvable"></a>

#### [a-revision-id-nothing-answers-to-is-refused-as-unresolvable](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

when a user granted deployment read reads a revision by an id nothing answers to, the call is rejected for the same reason as an id the user cannot see

Given

- one deployment holding 1 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.get_revision: user-1 reads a revision by an id nothing answers to

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading_revisions-a-user-granted-nothing-may-not-read-a-revision"></a>

#### [a-user-granted-nothing-may-not-read-a-revision](/tests/scenario/bai_scenario/manager/deployment/test_reading_revisions.py): pass

when a user with no deployment grant reads a revision by id, the call is rejected because the key cannot be decrypted

Given

- one deployment holding 1 revisions and a user with no deployment permission who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.get_revision: user-1 reads a revision by the id of the first revision of deployment-1

Then

- the call is rejected
  - rejected: GenericBadRequest

### project_search

<a id="searching-searching-a-project-finds-only-its-own-deployments"></a>

#### [searching-a-project-finds-only-its-own-deployments](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when deployments are split across two projects and a user granted read on only one side searches that project, only that project's deployments come back

Given

- deployments split between two projects and one user granted READ on deployments in one project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Project other-1
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment beside-1: replica count 1, has no revision yet
  - Deployment elsewhere-1: replica count 1, has no revision yet

When

- DeploymentAdapter.project_search: user-1 searches inside team-1

Then

- every deployment seeded in advance is counted, and nothing else
  - items = ['beside-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-a-project"></a>

#### [a-user-granted-nothing-may-not-search-a-project](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when a user without read permission on the project searches the project, the call is rejected for lack of permission

Given

- 3 deployments in the same project and one user of that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-2: replica count 1, has no revision yet

When

- DeploymentAdapter.project_search: user-1 searches inside team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-searching-my-own-finds-only-what-i-made"></a>

#### [searching-my-own-finds-only-what-i-made](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when two users each created a deployment in the same project and the one granted read in their own scope searches their own, only what they created comes back

Given

- deployments two users each created and one of them granted deployment read permission in their own scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user who can read deployments in their own scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-owner-1: applies only within the scope it is granted in
    - Role deployment-owner-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-owner-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment mine-1: replica count 1, has no revision yet
  - Deployment theirs-1: replica count 1, has no revision yet

When

- DeploymentAdapter.scoped_search: user-1 searches their own

Then

- every deployment seeded in advance is counted, and nothing else
  - items = ['mine-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-even-their-own"></a>

#### [a-user-granted-nothing-may-not-search-even-their-own](/tests/scenario/bai_scenario/manager/deployment/test_searching.py): pass

when a user not granted read in their own scope searches their own, the call is rejected for lack of permission; here too the permission checks it rather than only narrowing the scope

Given

- deployments two users each created and one of them with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment mine-1: replica count 1, has no revision yet
  - Deployment theirs-1: replica count 1, has no revision yet

When

- DeploymentAdapter.scoped_search: user-1 searches their own

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_access_tokens

<a id="searching_access_tokens-a-user-granted-deployment-read-searches-the-tokens"></a>

#### [a-user-granted-deployment-read-searches-the-tokens](/tests/scenario/bai_scenario/manager/deployment/test_searching_access_tokens.py): pass

when a user granted deployment read searches the access tokens the deployment holds with a filter, those tokens come back

Given

- one deployment holding 2 access tokens, and a user granted the READ permission on deployments, one more token on the same deployment, and one token on another deployment
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-1: has one deployment token

When

- DeploymentAdapter.search_access_tokens: user-1 searches the access tokens the deployment holds with one filter, one order and pagination

Then

- the token the filter excludes and the token on another deployment do not come back, and the tokens the deployment holds come back with their count
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the token seeded in advance
  - items[0].field_id: same as the id of the token seeded in advance
  - items[0].token = 'scenario-token'
  - items[0].expires_at = None
  - items[0].created_at: the time this run wrote
  - items[1].id: same as the id of the token seeded in advance
  - items[1].field_id: same as the id of the token seeded in advance
  - items[1].token = 'scenario-token'
  - items[1].expires_at = None
  - items[1].created_at: the time this run wrote

<a id="searching_access_tokens-a-user-granted-nothing-searches-no-token"></a>

#### [a-user-granted-nothing-searches-no-token](/tests/scenario/bai_scenario/manager/deployment/test_searching_access_tokens.py): pass

when a user granted nothing tries to search the access tokens the deployment holds, the search is rejected because the user lacks permission

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.search_access_tokens: user-1 searches the access tokens the deployment holds with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_policies

<a id="searching_policies-the-superadmin-searches-the-policies"></a>

#### [the-superadmin-searches-the-policies](/tests/scenario/bai_scenario/manager/deployment/test_searching_policies.py): pass

when the superadmin searches the deployment policies with a filter, the policy seeded in advance comes back. The requesting user of this row is the superadmin because the search is gated by the global role

Given

- one deployment holding one policy, and the superadmin, and one policy on another deployment
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-1: has one deployment policy

When

- DeploymentAdapter.search_policies: user-1 searches the deployment policies with one filter and pagination

Then

- the policy on another deployment the filter excludes does not come back, and the policy seeded in advance comes back with its count
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the policy seeded in advance
  - items[0].field_id: same as the id of the policy seeded in advance
  - items[0].deployment_id: same as the id of the deployment the policy sets
  - items[0].strategy_spec.strategy: same as the strategy of the policy seeded in advance
  - items[0].strategy_spec.max_surge = IntOrPercent(count=1, percent=None)
  - items[0].strategy_spec.max_unavailable = IntOrPercent(count=0, percent=None)
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching_policies-a-user-granted-nothing-searches-no-policy"></a>

#### [a-user-granted-nothing-searches-no-policy](/tests/scenario/bai_scenario/manager/deployment/test_searching_policies.py): pass

when a user granted nothing tries to search the deployment policies, the search is rejected because the user lacks the global role

Given

- one deployment holding one policy, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy

When

- DeploymentAdapter.search_policies: user-1 searches the deployment policies with one filter and pagination

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_replicas

<a id="searching_replicas-a-user-granted-deployment-read-searches-the-replica-with-traffic-enabled"></a>

#### [a-user-granted-deployment-read-searches-the-replica-with-traffic-enabled](/tests/scenario/bai_scenario/manager/deployment/test_searching_replicas.py): pass

when a user granted deployment read searches the replica of a route with traffic enabled, the replicas seeded in advance come back

Given

- one deployment holding one revision and 1 replica routes with traffic enabled, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.search_replicas: user-1 searches the replicas of deployment-1

Then

- the replica seeded in advance with traffic enabled comes back with its count
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the route seeded in advance
  - items[0].field_id: same as the id of the route seeded in advance
  - items[0].deployment_id: same as the id of the deployment the replica serves
  - items[0].revision_id: same as the id of the revision seeded in advance
  - items[0].session_id = None
  - items[0].readiness_status = 'NOT_CHECKED'
  - items[0].liveness_status = 'NOT_CHECKED'
  - items[0].activeness_status = 'INACTIVE'
  - items[0].status = 'provisioning'
  - items[0].traffic_status = 'active'
  - items[0].health_status = 'not_checked'
  - items[0].created_at: the time this run wrote

<a id="searching_replicas-a-user-granted-deployment-read-searches-the-replicas"></a>

#### [a-user-granted-deployment-read-searches-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_searching_replicas.py): pass

when a user granted deployment read searches the replicas of the deployment with a filter, the replicas seeded in advance come back

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ permission on deployments, one more replica route with traffic enabled, and one replica route on another deployment
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route
  - Deployment deployment-1: has one replica route
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-1: has one revision
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-1: has one replica group holding the session group
  - Deployment other-1: has one replica route

When

- DeploymentAdapter.search_replicas: user-1 searches the replicas of deployment-1 with one filter, one order and pagination

Then

- the replica the filter excludes and the replica on another deployment do not come back, and the replicas seeded in advance come back with their count
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the route seeded in advance
  - items[0].field_id: same as the id of the route seeded in advance
  - items[0].deployment_id: same as the id of the deployment the replica serves
  - items[0].revision_id: same as the id of the revision seeded in advance
  - items[0].session_id = None
  - items[0].readiness_status = 'NOT_CHECKED'
  - items[0].liveness_status = 'NOT_CHECKED'
  - items[0].activeness_status = 'INACTIVE'
  - items[0].status = 'provisioning'
  - items[0].traffic_status = 'inactive'
  - items[0].health_status = 'not_checked'
  - items[0].created_at: the time this run wrote

<a id="searching_replicas-a-user-granted-nothing-searches-no-replica"></a>

#### [a-user-granted-nothing-searches-no-replica](/tests/scenario/bai_scenario/manager/deployment/test_searching_replicas.py): pass

when a user granted nothing tries to search the replicas of the deployment, the search is rejected because the user lacks permission

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.search_replicas: user-1 searches the replicas of deployment-1 with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_revisions

<a id="searching_revisions-a-user-granted-read-counts-every-revision-of-a-deployment"></a>

#### [a-user-granted-read-counts-every-revision-of-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when a user granted read on a deployment holding three revisions searches that deployment's revisions, all three are counted

Given

- one deployment holding 3 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Deployment deployment-1: has one revision
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.search_revisions: user-1 searches the revisions of deployment-1

Then

- every revision seeded in advance is counted, and nothing else
  - items.id: same as the revisions counted
  - items.revision_number = [1, 2, 3]
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-another-deployments-revisions-stay-out-of-a-deployment-search"></a>

#### [another-deployments-revisions-stay-out-of-a-deployment-search](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when revisions are split across deployments in two projects and a user granted read on only one side searches that side's deployment revisions, only that side comes back

Given

- revisions are split between deployments in two projects, 2 and 1, and one user granted READ on deployments in one project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Project other-1
  - Deployment wanted-1: replica count 1, has no revision yet
  - Deployment elsewhere-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment wanted-1: has one revision
  - Deployment wanted-1: has one revision
  - Deployment elsewhere-1: has one revision

When

- DeploymentAdapter.search_revisions: user-1 searches the revisions of wanted-1

Then

- every revision seeded in advance is counted, and nothing else
  - items.id: same as the revisions counted
  - items.revision_number = [1, 2]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-filtering-revisions-by-number-leaves-only-that-one"></a>

#### [filtering-revisions-by-number-leaves-only-that-one](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

searching the revisions of a deployment holding three revisions filtered by number leaves only the one with that number

Given

- one deployment holding 3 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Deployment deployment-1: has one revision
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.search_revisions: user-1 searches the revisions of deployment-1 filtered by number 2

Then

- every revision seeded in advance is counted, and nothing else
  - items.id: same as the revisions counted
  - items.revision_number = [2]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-nothing-may-not-search-a-deployments-revisions"></a>

#### [a-user-granted-nothing-may-not-search-a-deployments-revisions](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when a user with no deployment grant searches a deployment's revisions, the call is rejected for lack of permission

Given

- one deployment holding 1 revisions and a user with no deployment permission who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.search_revisions: user-1 searches the revisions of deployment-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_routes

<a id="searching_routes-a-user-granted-deployment-read-searches-the-routes"></a>

#### [a-user-granted-deployment-read-searches-the-routes](/tests/scenario/bai_scenario/manager/deployment/test_searching_routes.py): pass

when a user granted deployment read searches the routes of the deployment with a filter, the routes seeded in advance come back

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ permission on deployments, one more replica route with traffic enabled, and one replica route on another deployment
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route
  - Deployment deployment-1: has one replica route
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-1: has one revision
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-1: has one replica group holding the session group
  - Deployment other-1: has one replica route

When

- DeploymentAdapter.search_routes: user-1 searches the routes of deployment-1 with one filter, one order and pagination

Then

- the route the filter excludes and the route on another deployment do not come back, and the routes seeded in advance come back with their count
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the route seeded in advance
  - items[0].field_id: same as the id of the route seeded in advance
  - items[0].deployment_id: same as the id of the deployment the route serves
  - items[0].session_id = None
  - items[0].status = 'provisioning'
  - items[0].health_status = 'not_checked'
  - items[0].traffic_ratio = 1.0
  - items[0].created_at: the time this run wrote
  - items[0].revision_id: same as the id of the revision seeded in advance
  - items[0].traffic_status = 'inactive'
  - items[0].error_data = {}

<a id="searching_routes-a-user-granted-nothing-searches-no-route"></a>

#### [a-user-granted-nothing-searches-no-route](/tests/scenario/bai_scenario/manager/deployment/test_searching_routes.py): pass

when a user granted nothing tries to search the routes of the deployment, the search is rejected because the user lacks permission

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.search_routes: user-1 searches the routes of deployment-1 with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_rules

<a id="searching_rules-a-user-granted-deployment-read-searches-the-rules"></a>

#### [a-user-granted-deployment-read-searches-the-rules](/tests/scenario/bai_scenario/manager/deployment/test_searching_rules.py): pass

when a user granted deployment read searches the auto-scaling rules the deployment holds with a filter, those rules come back

Given

- one deployment holding 2 auto-scaling rules, and a user granted the READ permission on deployments, one more rule with a different metric name on the same deployment, and one rule on another deployment
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment other-1: replica count 1, has no revision yet
  - Deployment other-1: has one auto-scaling rule

When

- DeploymentAdapter.search_rules: user-1 searches the auto-scaling rules the deployment holds with one filter, one order and pagination

Then

- the rule the filter excludes and the rule on another deployment do not come back, and the rules the deployment holds come back with their count
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the rule seeded in advance
  - items[0].field_id: same as the id of the rule seeded in advance
  - items[0].deployment_id: same as the id of the deployment the rule scales
  - items[0].metric_source = 'KERNEL'
  - items[0].metric_name = 'cpu_util'
  - items[0].min_threshold = None
  - items[0].max_threshold = None
  - items[0].step_size = 1
  - items[0].time_window = 60
  - items[0].min_replicas = None
  - items[0].max_replicas = None
  - items[0].prometheus_query_preset_id = None
  - items[0].created_at: the time this run wrote
  - items[0].last_triggered_at = None
  - items[1].id: same as the id of the rule seeded in advance
  - items[1].field_id: same as the id of the rule seeded in advance
  - items[1].deployment_id: same as the id of the deployment the rule scales
  - items[1].metric_source = 'KERNEL'
  - items[1].metric_name = 'cpu_util'
  - items[1].min_threshold = None
  - items[1].max_threshold = None
  - items[1].step_size = 1
  - items[1].time_window = 60
  - items[1].min_replicas = None
  - items[1].max_replicas = None
  - items[1].prometheus_query_preset_id = None
  - items[1].created_at: the time this run wrote
  - items[1].last_triggered_at = None

<a id="searching_rules-a-user-granted-nothing-searches-no-rule"></a>

#### [a-user-granted-nothing-searches-no-rule](/tests/scenario/bai_scenario/manager/deployment/test_searching_rules.py): pass

when a user granted nothing tries to search the auto-scaling rules the deployment holds, the search is rejected because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.search_rules: user-1 searches the auto-scaling rules the deployment holds with one filter, one order and pagination

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_current_revision

<a id="reading-a-deployment-holding-no-revision-answers-nothing-as-its-current-one"></a>

#### [a-deployment-holding-no-revision-answers-nothing-as-its-current-one](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

reading the current revision of a deployment holding no revision is rejected because there is no current revision

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get_current_revision: user-1 reads the current revision of deployment-1

Then

- the call is rejected
  - rejected: DeploymentRevisionNotFound

### add_revision

<a id="adding_revisions-a-revision-added-without-resources-runs-on-one-node-with-no-slot"></a>

#### [a-revision-added-without-resources-runs-on-one-node-with-no-slot](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

adding a revision without resources and cluster when there is neither a preset nor a required slot brings back a revision on one node with size 1 and no resource slot

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1 without resources and cluster

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - deployment_id: same as the deployment seeded in advance
  - revision_number = 1
  - image_id: same as the image seeded in advance
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = []
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: the time this run wrote
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-a-user-granted-create-adds-the-first-revision"></a>

#### [a-user-granted-create-adds-the-first-revision](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a user granted create adds a revision with every setting to a deployment that has no revision, the revision numbered 1 comes back with exactly the settings that were given

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - deployment_id: same as the deployment seeded in advance
  - revision_number = 1
  - image_id: same as the image seeded in advance
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: the time this run wrote
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-the-next-revision-is-numbered-one-past-the-last"></a>

#### [the-next-revision-is-numbered-one-past-the-last](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

adding a revision to a deployment that holds one revision brings back the revision numbered 2

Given

- one deployment holding 1 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - deployment_id: same as the deployment seeded in advance
  - revision_number = 2
  - image_id: same as the image seeded in advance
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: the time this run wrote
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-adds-a-revision-to-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a superadmin holding no grant on the deployment or on their own model vfolder adds a revision to another user's deployment, the revision is added; the role passes through both the deployment permission and the vfolder permission

Given

- one deployment another user created and a superadmin with permission on neither the deployment nor their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment theirs-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to theirs-1

Then

- the whole revision comes back
  - id: skipped: the database generates it
  - deployment_id: same as the deployment seeded in advance
  - revision_number = 1
  - image_id: same as the image seeded in advance
  - cluster_config = ClusterConfigInfoDTO(mode='SINGLE_NODE', size=1)
  - resource_config.resource_group_name = 'resource-group-1'
  - resource_config.resource_slots = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - resource_config.resource_opts = None
  - model_runtime_config.runtime_variant_id: same as the runtime variant seeded in advance
  - model_runtime_config.inference_runtime_config = None
  - model_runtime_config.environ = None
  - model_runtime_config.runtime_variant_preset_values = []
  - model_mount_config.vfolder_id: same as the model vfolder seeded in advance
  - model_mount_config.mount_destination = '/models'
  - model_mount_config.definition_path = ''
  - model_mount_config.subpath = None
  - model_definition = ModelDefinitionInfoDTO(models=[ModelConfigInfoDTO(name='served', model_path='/models', service=None, metadata=None)])
  - created_at: the time this run wrote
  - extra_mounts = []
  - revision_preset_id = None

<a id="adding_revisions-a-model-folder-the-caller-may-not-read-is-not-found"></a>

#### [a-model-folder-the-caller-may-not-read-is-not-found](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a user granted create on the deployment but not read on the model vfolder adds a revision with that vfolder, the call is rejected because the vfolder is not found

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who has no permission to read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the call is rejected
  - rejected: VFolderNotFound

<a id="adding_revisions-a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused"></a>

#### [a-mount-beyond-what-the-caller-holds-on-the-folder-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a user who borrowed another user's model vfolder as read-only adds a revision that mounts it read-write, the call is rejected because it exceeds the vfolder permission

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments borrowing another user's model vfolder as read-only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions, folders can be placed on local:volume1
    - regular user user-2: has their own keypair and personal project
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use, is mounted for others as ro
    - vfolder share offer share-1: offered under the READ permission, not answered yet
    - vfolder share offer share-1: the recipient accepts it
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the call is rejected
  - rejected: VFolderPermissionError

<a id="adding_revisions-a-revision-missing-a-required-slot-is-refused"></a>

#### [a-revision-missing-a-required-slot-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a slot every revision must fill is set and a revision is added without it, the call is rejected because the input is wrong

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: every revision must fill it
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="adding_revisions-a-revision-with-no-image-from-any-layer-is-refused"></a>

#### [a-revision-with-no-image-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

adding a revision without an image and without a preset is rejected because the input is wrong

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1 without the image

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="adding_revisions-a-revision-with-no-model-definition-from-any-layer-is-refused"></a>

#### [a-revision-with-no-model-definition-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

adding a revision with a runtime variant that does not read vfolder files, without a model definition and without a preset, is rejected in model definition validation because a model has no name

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1 without the model definition

Then

- the call is rejected
  - rejected: BackendAISchemaValidationFailed

<a id="adding_revisions-a-revision-with-no-runtime-variant-from-any-layer-is-refused"></a>

#### [a-revision-with-no-runtime-variant-from-any-layer-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

adding a revision without a runtime variant and without a preset is rejected because the input is wrong

Given

- one deployment holding 0 revisions and a user granted CREATE on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1 without the runtime variant

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="adding_revisions-a-user-granted-only-read-may-not-add-a-revision"></a>

#### [a-user-granted-only-read-may-not-add-a-revision](/tests/scenario/bai_scenario/manager/deployment/test_adding_revisions.py): pass

when a user granted only read on the deployment adds a revision, the call is rejected for lack of permission

Given

- one deployment holding 0 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled

When

- DeploymentAdapter.add_revision: user-1 adds a revision to deployment-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### bulk_delete_access_tokens

<a id="retiring_access_tokens-a-user-granted-deployment-purge-purges-tokens-at-once"></a>

#### [a-user-granted-deployment-purge-purges-tokens-at-once](/tests/scenario/bai_scenario/manager/deployment/test_retiring_access_tokens.py): pass

when a user granted deployment purge purges several access tokens the deployment holds at once, the ids of those tokens come back

Given

- one deployment holding 2 access tokens, and a user granted the HARD_DELETE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted HARD_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: HARD_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.bulk_delete_access_tokens: user-1 purges 2 tokens at once

Then

- the ids of the purged tokens come back
  - ids count = 2
  - ids[0]: same as the id of the token seeded in advance
  - ids[1]: same as the id of the token seeded in advance

<a id="retiring_access_tokens-a-user-granted-nothing-purges-no-token-at-once"></a>

#### [a-user-granted-nothing-purges-no-token-at-once](/tests/scenario/bai_scenario/manager/deployment/test_retiring_access_tokens.py): pass

when a user granted nothing tries to purge several access tokens the deployment holds at once, nothing is purged and the id list comes back empty

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.bulk_delete_access_tokens: user-1 purges 2 tokens at once

Then

- nothing is purged and the id list comes back empty
  - ids = []

### create

<a id="creating-a-deployment-made-without-a-name-is-named-after-its-maker"></a>

#### [a-deployment-made-without-a-name-is-named-after-its-maker](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

creating a deployment without a name names it after the user who created it

Given

- a project that can hold deployments and one user granted CREATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1

When

- DeploymentAdapter.create: user-1 creates a deployment without a name in team-1

Then

- the whole deployment just created comes back
  - id: skipped: the database generates it
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name: the name given after its maker
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user who created it
  - options: same as the resource group defaults
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-a-user-granted-create-in-a-project-makes-a-deployment-there"></a>

#### [a-user-granted-create-in-a-project-makes-a-deployment-there](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

when a user granted create in a project creates a deployment, a deployment that belongs to the project and is owned by the requesting user is created with no revision

Given

- a project that can hold deployments and one user granted CREATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1

When

- DeploymentAdapter.create: user-1 creates a deployment named serving in team-1

Then

- the whole deployment just created comes back
  - id: skipped: the database generates it
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 2
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user who created it
  - options: same as the resource group defaults
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-turning-enforcement-off-lets-a-user-create-a-deployment"></a>

#### [turning-enforcement-off-lets-a-user-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

turning entity permission enforcement off lets a user with no grant create a deployment, because the permission graph checks this operation, not the role

Given

- a project that can hold deployments and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project

When

- DeploymentAdapter.create: user-1 creates a deployment named serving in team-1

Then

- the whole deployment just created comes back
  - id: skipped: the database generates it
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'serving'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user who created it
  - options: same as the resource group defaults
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = DeploymentPolicyInfo(strategy=<DeploymentStrategy.ROLLING: 'ROLLING'>, rolling_update=RollingUpdateConfigInfo(max_surge=IntOrPercent(count=2, percent=None), max_unavailable=IntOrPercent(count=0, percent=None)), blue_green=None)

<a id="creating-a-create-grant-in-another-project-does-not-reach-this-one"></a>

#### [a-create-grant-in-another-project-does-not-reach-this-one](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

creating a deployment in a project other than the one where the create grant was given is rejected for lack of permission

Given

- a project to hold the deployment and one user granted CREATE on deployments in another project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1

When

- DeploymentAdapter.create: user-1 creates a deployment named serving in team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="creating-a-user-granted-nothing-may-not-create-a-deployment"></a>

#### [a-user-granted-nothing-may-not-create-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_creating.py): pass

when a user granted no deployment permission creates a deployment, the call is rejected for lack of permission

Given

- a project that can hold deployments and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project

When

- DeploymentAdapter.create: user-1 creates a deployment named serving in team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create_access_token

<a id="creating_access_tokens-a-user-granted-deployment-create-makes-no-token"></a>

#### [a-user-granted-deployment-create-makes-no-token](/tests/scenario/bai_scenario/manager/deployment/test_creating_access_tokens.py): pass

when a user granted deployment create tries to make an access token of the deployment, the create is rejected because the deployment's scaling group has no proxy target configured

Given

- one deployment holding 2 access tokens, and a user granted the CREATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.create_access_token: user-1 makes one access token of the deployment

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### create_rule

<a id="creating_rules-a-user-granted-deployment-create-makes-a-rule"></a>

#### [a-user-granted-deployment-create-makes-a-rule](/tests/scenario/bai_scenario/manager/deployment/test_creating_rules.py): pass

when a user granted deployment create makes an auto-scaling rule of the deployment, the rule made comes back

Given

- one deployment holding 2 auto-scaling rules, and a user granted the CREATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted CREATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: CREATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.create_rule: user-1 makes one auto-scaling rule of the deployment

Then

- the whole rule made comes back
  - id: skipped: the database generates it
  - field_id: skipped: the database generates it
  - deployment_id: same as the id of the deployment the rule scales
  - metric_source = 'KERNEL'
  - metric_name = 'made-rule'
  - min_threshold = None
  - max_threshold = None
  - step_size = 1
  - time_window = 60
  - min_replicas = None
  - max_replicas = None
  - prometheus_query_preset_id = None
  - created_at: the time this run wrote
  - last_triggered_at = None

<a id="creating_rules-a-user-granted-nothing-makes-no-rule"></a>

#### [a-user-granted-nothing-makes-no-rule](/tests/scenario/bai_scenario/manager/deployment/test_creating_rules.py): pass

when a user granted nothing tries to make an auto-scaling rule of the deployment, the create is rejected because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.create_rule: user-1 makes one auto-scaling rule of the deployment

Then

- the call is rejected
  - rejected: NotEnoughPermission

### delete

<a id="retiring-a-user-granted-soft-delete-retires-a-deployment"></a>

#### [a-user-granted-soft-delete-retires-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

when a user granted soft-delete deletes a deployment, the response says the deployment's deletion has started

Given

- one existing deployment and one user granted SOFT_DELETE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted SOFT_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: SOFT_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.delete: user-1 deletes deployment-1

Then

- the response carries the deployment whose deletion has started
  - id: same as the deployment seeded in advance

<a id="retiring-the-superadmin-retires-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-retires-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

when a superadmin holding no grant deletes another user's deployment, the response says the deployment's deletion has started; the role passes through the permission graph

Given

- one deployment another user created and one superadmin with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment theirs-1: replica count 1, has no revision yet

When

- DeploymentAdapter.delete: user-1 deletes theirs-1

Then

- the response carries the deployment whose deletion has started
  - id: same as the deployment seeded in advance

<a id="retiring-a-user-granted-only-update-may-not-retire-a-deployment"></a>

#### [a-user-granted-only-update-may-not-retire-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

when a user granted only update and not soft-delete deletes a deployment, the call is rejected for lack of permission; deletion is a different operation from update

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.delete: user-1 deletes deployment-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [retiring-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_retiring.py): pass

when a superadmin deletes an id nothing answers to, the call is rejected as not found

Given

- one existing deployment and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.delete: user-1 deletes an id nothing answers to

Then

- the call is rejected
  - rejected: EndpointNotFound

### get

<a id="reading-a-user-granted-read-reads-a-deployment-by-id"></a>

#### [a-user-granted-read-reads-a-deployment-by-id](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

when a deployment exists and a user granted read reads it by id, that deployment comes back in the response

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get: user-1 reads deployment-1

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="reading-the-superadmin-reads-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-reads-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

when a superadmin holding no grant reads another user's deployment by id, that deployment comes back in the response; the role passes through the permission graph

Given

- one deployment another user created and one superadmin with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment theirs-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get: user-1 reads theirs-1

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'theirs-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="reading-a-user-granted-nothing-may-not-read-a-deployment"></a>

#### [a-user-granted-nothing-may-not-read-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

when the same deployment exists and a user with no grant reads it, the call is rejected for lack of permission

Given

- one existing deployment and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get: user-1 reads deployment-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

when a superadmin reads by an id nothing answers to, the call is rejected as not found; only someone who passes the permission check sees this response

Given

- one existing deployment and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get: user-1 reads by an id nothing answers to

Then

- the call is rejected
  - rejected: EndpointNotFound

<a id="reading-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"></a>

#### [an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/deployment/test_reading.py): pass

when a user granted read reads by an id nothing answers to, the call is rejected for lack of permission rather than as not found, because no permission is held on a row that does not exist

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.get: user-1 reads by an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_policy

<a id="reading_policy-a-user-granted-deployment-read-reads-the-policy"></a>

#### [a-user-granted-deployment-read-reads-the-policy](/tests/scenario/bai_scenario/manager/deployment/test_reading_policy.py): pass

when a user granted deployment read reads the policy the deployment holds, that policy comes back

Given

- one deployment holding one policy, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy

When

- DeploymentAdapter.get_policy: user-1 reads the policy the deployment holds

Then

- the policy the deployment holds comes back whole
  - id: same as the id of the policy seeded in advance
  - field_id: same as the id of the policy seeded in advance
  - deployment_id: same as the id of the deployment the policy sets
  - strategy_spec.strategy: same as the strategy of the policy seeded in advance
  - strategy_spec.max_surge = IntOrPercent(count=1, percent=None)
  - strategy_spec.max_unavailable = IntOrPercent(count=0, percent=None)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading_policy-a-user-granted-nothing-reads-no-policy"></a>

#### [a-user-granted-nothing-reads-no-policy](/tests/scenario/bai_scenario/manager/deployment/test_reading_policy.py): pass

when a user granted nothing tries to read the policy the deployment holds, the read is rejected because the user lacks permission

Given

- one deployment holding one policy, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment policy

When

- DeploymentAdapter.get_policy: user-1 reads the policy the deployment holds

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_rule

<a id="reading_rules-a-user-granted-deployment-read-reads-a-rule"></a>

#### [a-user-granted-deployment-read-reads-a-rule](/tests/scenario/bai_scenario/manager/deployment/test_reading_rules.py): pass

when a user granted deployment read reads one of the rules seeded in advance by id, that rule comes back

Given

- one deployment holding 2 auto-scaling rules, and a user granted the READ permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.get_rule: user-1 reads one of the rules seeded in advance by id

Then

- the whole rule read comes back
  - id: same as the id of the rule seeded in advance
  - field_id: same as the id of the rule seeded in advance
  - deployment_id: same as the id of the deployment the rule scales
  - metric_source = 'KERNEL'
  - metric_name = 'cpu_util'
  - min_threshold = None
  - max_threshold = None
  - step_size = 1
  - time_window = 60
  - min_replicas = None
  - max_replicas = None
  - prometheus_query_preset_id = None
  - created_at: the time this run wrote
  - last_triggered_at = None

<a id="reading_rules-a-user-granted-nothing-reads-no-rule"></a>

#### [a-user-granted-nothing-reads-no-rule](/tests/scenario/bai_scenario/manager/deployment/test_reading_rules.py): pass

when a user granted nothing tries to read one of the rules seeded in advance by id, the lookup that finds the deployment holding the rule is rejected

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.get_rule: user-1 reads one of the rules seeded in advance by id

Then

- the call is rejected
  - rejected: GenericBadRequest

### partial_bulk_purge_access_tokens

<a id="partial_bulk_access_tokens-a-user-granted-nothing-purges-none-of-several-tokens"></a>

#### [a-user-granted-nothing-purges-none-of-several-tokens](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_access_tokens.py): pass

when a user with no grant tries to purge several deployment tokens at once, nothing is purged and every token comes back in the failed list because the user lacks permission

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.partial_bulk_purge_access_tokens: user-1 purges 2 deployment tokens at once

Then

- no token is processed and every token comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the token seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the token seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_access_tokens-purging-several-tokens-answers-for-the-missing-one"></a>

#### [purging-several-tokens-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_access_tokens.py): pass

when a user granted deployment purge purges two deployment tokens and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- one deployment holding 2 access tokens, and a user granted the HARD_DELETE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted HARD_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: HARD_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.partial_bulk_purge_access_tokens: user-1 purges 2 deployment tokens and one unknown id at once

Then

- every token comes back in the processed list, and the missing id comes back in the failed list with a reason that it does not exist
  - successes count = 2
  - successes[0].id: same as the id of the token seeded in advance
  - successes[1].id: same as the id of the token seeded in advance
  - failed count = 1
  - failed[0].id: same as the nonexistent id sent in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_purge_rules

<a id="partial_bulk_auto_scaling_rules-a-deployment-editor-purges-none-of-several-rules"></a>

#### [a-deployment-editor-purges-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

when a user granted only deployment update tries to purge several auto-scaling rules at once, nothing is purged and every rule comes back in the failed list because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user granted the UPDATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 purges 2 auto-scaling rules at once

Then

- no rule is processed and every rule comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the rule seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the rule seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_auto_scaling_rules-a-user-granted-nothing-purges-none-of-several-rules"></a>

#### [a-user-granted-nothing-purges-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

when a user with no grant tries to purge several auto-scaling rules at once, nothing is purged and every rule comes back in the failed list because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 purges 2 auto-scaling rules at once

Then

- no rule is processed and every rule comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the rule seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the rule seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_auto_scaling_rules-purging-several-rules-answers-for-the-missing-one"></a>

#### [purging-several-rules-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

when a user granted deployment purge purges two auto-scaling rules and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it

Given

- one deployment holding 2 auto-scaling rules, and a user granted the HARD_DELETE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted HARD_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: HARD_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.partial_bulk_purge_rules: user-1 purges 2 auto-scaling rules and one unknown id at once

Then

- every rule comes back with metric name 'cpu_util', and the missing id comes back in the failed list with a reason that it does not exist
  - successes count = 2
  - successes[0].id: same as the id of the rule seeded in advance
  - successes[0].metric_name = 'cpu_util'
  - successes[1].id: same as the id of the rule seeded in advance
  - successes[1].metric_name = 'cpu_util'
  - failed count = 1
  - failed[0].id: same as the nonexistent id sent in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update_rules

<a id="partial_bulk_auto_scaling_rules-a-deployment-editor-edits-several-rules-at-once"></a>

#### [a-deployment-editor-edits-several-rules-at-once](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

when a user granted deployment update changes the metric name of several auto-scaling rules at once, every rule comes back with the new name and nothing failed

Given

- one deployment holding 2 auto-scaling rules, and a user granted the UPDATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.partial_bulk_update_rules: user-1 changes the metric name of 2 auto-scaling rules at once

Then

- every rule comes back with metric name 'memory_util', and none failed
  - successes count = 2
  - successes[0].id: same as the id of the rule seeded in advance
  - successes[0].metric_name = 'memory_util'
  - successes[1].id: same as the id of the rule seeded in advance
  - successes[1].metric_name = 'memory_util'
  - failed = []

<a id="partial_bulk_auto_scaling_rules-a-user-granted-nothing-edits-none-of-several-rules"></a>

#### [a-user-granted-nothing-edits-none-of-several-rules](/tests/scenario/bai_scenario/manager/deployment/test_partial_bulk_auto_scaling_rules.py): pass

when a user with no grant tries to update several auto-scaling rules at once, nothing is updated and every rule comes back in the failed list because the user lacks permission

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.partial_bulk_update_rules: user-1 changes the metric name of 2 auto-scaling rules at once

Then

- no rule is processed and every rule comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the rule seeded in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the rule seeded in advance
  - failed[1].message: a reason containing 'Insufficient permission'

### purge_access_token

<a id="retiring_access_tokens-a-user-granted-deployment-purge-purges-a-token"></a>

#### [a-user-granted-deployment-purge-purges-a-token](/tests/scenario/bai_scenario/manager/deployment/test_retiring_access_tokens.py): pass

when a user granted deployment read and purge purges one of the access tokens the deployment holds, the id of that token comes back. The purge reads the deployment first, so read is also required

Given

- one deployment holding 2 access tokens, and a user granted the READ, HARD_DELETE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ, HARD_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - Role deployment-user-1: HARD_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.purge_access_token: user-1 purges one of the tokens seeded in advance

Then

- the id of the purged token comes back
  - id: same as the id of the token seeded in advance
  - field_id: same as the id of the token seeded in advance

<a id="retiring_access_tokens-a-user-granted-nothing-purges-no-token"></a>

#### [a-user-granted-nothing-purges-no-token](/tests/scenario/bai_scenario/manager/deployment/test_retiring_access_tokens.py): pass

when a user granted nothing tries to purge one of the access tokens the deployment holds, the lookup that finds the deployment holding the token is rejected

Given

- one deployment holding 2 access tokens, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one deployment token
  - Deployment deployment-1: has one deployment token

When

- DeploymentAdapter.purge_access_token: user-1 purges one of the tokens seeded in advance

Then

- the call is rejected
  - rejected: GenericBadRequest

### purge_rule

<a id="retiring_rules-a-user-granted-deployment-purge-purges-a-rule"></a>

#### [a-user-granted-deployment-purge-purges-a-rule](/tests/scenario/bai_scenario/manager/deployment/test_retiring_rules.py): pass

when a user granted deployment read and purge purges one of the auto-scaling rules the deployment holds, the id of that rule comes back. The purge reads the deployment first, so read is also required

Given

- one deployment holding 2 auto-scaling rules, and a user granted the READ, HARD_DELETE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ, HARD_DELETE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - Role deployment-user-1: HARD_DELETE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.purge_rule: user-1 purges one of the rules seeded in advance

Then

- the id of the purged rule comes back
  - id: same as the id of the rule seeded in advance
  - field_id: same as the id of the rule seeded in advance

<a id="retiring_rules-a-user-granted-nothing-purges-no-rule"></a>

#### [a-user-granted-nothing-purges-no-rule](/tests/scenario/bai_scenario/manager/deployment/test_retiring_rules.py): pass

when a user granted nothing tries to purge one of the auto-scaling rules the deployment holds, the lookup that finds the deployment holding the rule is rejected

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.purge_rule: user-1 purges one of the rules seeded in advance

Then

- the call is rejected
  - rejected: GenericBadRequest

### replace_options

<a id="options-a-user-granted-update-replaces-the-options-whole"></a>

#### [a-user-granted-update-replaces-the-options-whole](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

when a user granted update replaces the options with the defaults and per-handler settings, what was given becomes the new options as a whole and the response carries only those options

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with the per-handler settings check-replica-deployments

Then

- only the replaced options come back
  - deployment_id: same as the deployment seeded in advance
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = [('check-replica-deployments', None, 1)]
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

<a id="options-replacing-with-a-strict-policy-keeps-it-strict"></a>

#### [replacing-with-a-strict-policy-keeps-it-strict](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

replacing the options with the selection policy STRICT keeps that policy on the new options

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with the selection policy strict and only the defaults

Then

- only the replaced options come back
  - deployment_id: same as the deployment seeded in advance
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-replacing-with-no-handler-entry-drops-the-inherited-ones"></a>

#### [replacing-with-no-handler-entry-drops-the-inherited-ones](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

replacing the options of a deployment that holds inherited per-handler settings with only the defaults leaves none of the inherited settings

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with only the defaults

Then

- only the replaced options come back
  - deployment_id: same as the deployment seeded in advance
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

<a id="options-replacing-without-a-policy-keeps-the-stored-one"></a>

#### [replacing-without-a-policy-keeps-the-stored-one](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

replacing the options of a deployment whose selection policy is STRICT without a policy keeps it STRICT

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet, the selection policy is strict

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with only the defaults

Then

- only the replaced options come back
  - deployment_id: same as the deployment seeded in advance
  - options.handler_options.default.timeout_sec = 600
  - options.handler_options.default.max_retry_count = 3
  - options.handler_options.by_handler = []
  - options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-a-user-granted-only-read-may-not-replace-the-options"></a>

#### [a-user-granted-only-read-may-not-replace-the-options](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

when a user granted only read replaces the options, the call is rejected for lack of permission

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with the per-handler settings check-replica-deployments

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="options-naming-a-handler-twice-is-refused"></a>

#### [naming-a-handler-twice-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

replacing the options with the same handler name twice is rejected because the input is wrong

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with the per-handler settings check-replica-deployments, check-replica-deployments

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="options-naming-an-unregistered-handler-is-refused"></a>

#### [naming-an-unregistered-handler-is-refused](/tests/scenario/bai_scenario/manager/deployment/test_options.py): pass

replacing the options with an unregistered handler name is rejected because the input is wrong

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.replace_options: user-1 replaces the options of deployment-1 with the per-handler settings no-such-handler

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### search_revision_resource_slots

<a id="searching_revisions-a-user-granted-read-counts-every-slot-a-revision-allocates"></a>

#### [a-user-granted-read-counts-every-slot-a-revision-allocates](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when a user granted read on a deployment holding a revision that allocates two slots searches that revision's slots, both are counted

Given

- one deployment holding 1 revisions and a user granted READ on deployments who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.search_revision_resource_slots: user-1 searches the slots allocated by the first revision of deployment-1

Then

- every slot a revision holds is counted
  - items = [('cpu', Decimal('1')), ('mem', Decimal('1073741824'))]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_revisions-a-user-granted-nothing-may-not-search-a-revisions-slots"></a>

#### [a-user-granted-nothing-may-not-search-a-revisions-slots](/tests/scenario/bai_scenario/manager/deployment/test_searching_revisions.py): pass

when a user with no deployment grant searches a deployment revision's slots, the call is rejected with a response that the revision is not found

Given

- one deployment holding 1 revisions and a user with no deployment permission who can read their own model vfolder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- DeploymentAdapter.search_revision_resource_slots: user-1 searches the slots allocated by the first revision of deployment-1

Then

- the call is rejected
  - rejected: GenericBadRequest

### sync_replicas

<a id="syncing-a-user-granted-update-starts-syncing-the-replicas"></a>

#### [a-user-granted-update-starts-syncing-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py): pass

when a user granted update asks to sync the replicas, the response says syncing has started

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 2, has no revision yet

When

- DeploymentAdapter.sync_replicas: user-1 asks deployment-1 to sync its replicas

Then

- the response says syncing the replicas has started
  - success = True

<a id="syncing-a-user-granted-only-read-may-not-sync-the-replicas"></a>

#### [a-user-granted-only-read-may-not-sync-the-replicas](/tests/scenario/bai_scenario/manager/deployment/test_syncing.py): pass

when a user granted only read asks to sync the replicas, the call is rejected for lack of permission

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.sync_replicas: user-1 asks deployment-1 to sync its replicas

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-opens-a-deployment-to-the-public"></a>

#### [a-user-granted-update-opens-a-deployment-to-the-public](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a user granted update changes a deployment that is not public to public, the state comes back changed to public

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates deployment-1 with opening it to the public

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = True
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-update-raises-the-replica-count"></a>

#### [a-user-granted-update-raises-the-replica-count](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a user granted update raises the replica count, the intended replica count becomes the new value

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates deployment-1 with replica count to 3

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 3
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-update-renames-a-deployment"></a>

#### [a-user-granted-update-renames-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a user granted update changes the name, only the name becomes the new value and everything else stays the same

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates deployment-1 with name to renamed

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-clearing-the-tags-of-a-deployment-leaves-none"></a>

#### [clearing-the-tags-of-a-deployment-leaves-none](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

clearing the tags of a deployment that holds tags leaves no tag

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet, tagged keep

When

- DeploymentAdapter.update: user-1 updates deployment-1 with clearing the tags

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'deployment-1'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-the-superadmin-renames-anothers-deployment-without-a-grant"></a>

#### [the-superadmin-renames-anothers-deployment-without-a-grant](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a superadmin holding no grant changes the name of a deployment another user created, only the name becomes the new value; the role passes through the permission graph

Given

- one deployment another user created and one superadmin with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Deployment theirs-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates theirs-1 with name to renamed

Then

- the whole deployment seeded in advance comes back
  - id: same as the deployment seeded in advance
  - metadata.project_id: same as the project seeded in advance
  - metadata.domain_name = 'home-1'
  - metadata.name = 'renamed'
  - metadata.status = <ModelDeploymentStatus.PENDING: 'PENDING'>
  - metadata.tags = []
  - metadata.resource_group_name = 'resource-group-1'
  - metadata.created_at: the time this run wrote
  - metadata.updated_at: the time this run wrote
  - network_access.endpoint_url = None
  - network_access.preferred_domain_name = None
  - network_access.open_to_public = False
  - replica_state.desired_replica_count = 1
  - replica_state.replica_ids = []
  - default_deployment_strategy.type = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - created_user_id: same as the user holding the seeded deployment
  - options: same as the options of the deployment seeded in advance
  - scaling_state = <ScalingState.STABLE: 'stable'>
  - current_revision_id = None
  - deploying_revision_id = None
  - policy = None

<a id="editing-a-user-granted-only-read-may-not-update-a-deployment"></a>

#### [a-user-granted-only-read-may-not-update-a-deployment](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a user granted only read updates a deployment, the call is rejected for lack of permission

Given

- one existing deployment and one user granted READ on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates deployment-1 with name to renamed

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [updating-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/deployment/test_editing.py): pass

when a superadmin updates an id nothing answers to, the call is rejected as not found

Given

- one existing deployment and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.update: user-1 updates an id nothing answers to with name to renamed

Then

- the call is rejected
  - rejected: EndpointNotFound

### update_route_traffic

<a id="editing_route_traffic-a-user-granted-deployment-update-opens-the-traffic"></a>

#### [a-user-granted-deployment-update-opens-the-traffic](/tests/scenario/bai_scenario/manager/deployment/test_editing_route_traffic.py): pass

when a user granted deployment read and update turns the traffic of a route on, the route with its traffic turned on comes back. The traffic change reads the deployment first, so read is also required

Given

- one deployment holding one revision and 1 replica routes, and a user granted the READ, UPDATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ, UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.update_route_traffic: user-1 turns the traffic of a route of deployment-1 to active

Then

- the route with its traffic turned on comes back whole
  - id: same as the id of the route seeded in advance
  - field_id: same as the id of the route seeded in advance
  - deployment_id: same as the id of the deployment the route serves
  - session_id = None
  - status = 'provisioning'
  - health_status = 'not_checked'
  - traffic_ratio = 1.0
  - created_at: the time this run wrote
  - revision_id: same as the id of the revision seeded in advance
  - traffic_status = 'active'
  - error_data = {}

<a id="editing_route_traffic-a-user-granted-nothing-changes-no-traffic"></a>

#### [a-user-granted-nothing-changes-no-traffic](/tests/scenario/bai_scenario/manager/deployment/test_editing_route_traffic.py): pass

when a user granted nothing tries to turn the traffic of a route, the lookup that finds the deployment holding the route is rejected

Given

- one deployment holding one revision and 1 replica routes, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - regular user user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica route

When

- DeploymentAdapter.update_route_traffic: user-1 turns the traffic of a route of deployment-1 to active

Then

- the call is rejected
  - rejected: GenericBadRequest

### update_rule

<a id="updating_rules-a-user-granted-deployment-update-edits-a-rule"></a>

#### [a-user-granted-deployment-update-edits-a-rule](/tests/scenario/bai_scenario/manager/deployment/test_updating_rules.py): pass

when a user granted deployment read and update edits one of the rules seeded in advance, the rule edited comes back. The edit reads the deployment first, so read is also required

Given

- one deployment holding 2 auto-scaling rules, and a user granted the READ, UPDATE permission on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted READ, UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: READ allowed on every deployment
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.update_rule: user-1 edits the step size and time window of one of the rules seeded in advance

Then

- the whole rule edited comes back
  - id: same as the id of the rule seeded in advance
  - field_id: same as the id of the rule seeded in advance
  - deployment_id: same as the id of the deployment the rule scales
  - metric_source = 'KERNEL'
  - metric_name = 'cpu_util'
  - min_threshold = None
  - max_threshold = None
  - step_size = 2
  - time_window = 120
  - min_replicas = None
  - max_replicas = None
  - prometheus_query_preset_id = None
  - created_at: the time this run wrote
  - last_triggered_at = None

<a id="updating_rules-a-user-granted-nothing-edits-no-rule"></a>

#### [a-user-granted-nothing-edits-no-rule](/tests/scenario/bai_scenario/manager/deployment/test_updating_rules.py): pass

when a user granted nothing tries to edit one of the rules seeded in advance, the lookup that finds the deployment holding the rule is rejected

Given

- one deployment holding 2 auto-scaling rules, and a user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Deployment deployment-1: has one auto-scaling rule
  - Deployment deployment-1: has one auto-scaling rule

When

- DeploymentAdapter.update_rule: user-1 edits the step size and time window of one of the rules seeded in advance

Then

- the call is rejected
  - rejected: GenericBadRequest

### upsert_policy

<a id="upserting_policy-a-user-granted-deployment-update-puts-the-policy"></a>

#### [a-user-granted-deployment-update-puts-the-policy](/tests/scenario/bai_scenario/manager/deployment/test_upserting_policy.py): pass

when a user granted deployment update puts a policy on the deployment, the policy put comes back. The upsert replaces an existing policy, so the call is gated by update

Given

- one existing deployment and one user granted UPDATE on deployments
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted UPDATE on deployments
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role deployment-user-1: applies only within the scope it is granted in
    - Role deployment-user-1: UPDATE allowed on every deployment
    - regular user user-1: holds Role deployment-user-1
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.upsert_policy: user-1 puts a rolling-update policy on the deployment

Then

- the whole policy put comes back
  - id: skipped: the database generates it
  - field_id: skipped: the database generates it
  - deployment_id: same as the id of the deployment the policy was put on
  - strategy_spec.strategy = <DeploymentStrategy.ROLLING: 'ROLLING'>
  - strategy_spec.max_surge = IntOrPercent(count=None, percent=0.5)
  - strategy_spec.max_unavailable = IntOrPercent(count=None, percent=0.0)
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting_policy-a-user-granted-nothing-puts-no-policy"></a>

#### [a-user-granted-nothing-puts-no-policy](/tests/scenario/bai_scenario/manager/deployment/test_upserting_policy.py): pass

when a user granted nothing tries to put a policy on the deployment, the upsert is rejected because the user lacks permission

Given

- one existing deployment and one user with no deployment permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet

When

- DeploymentAdapter.upsert_policy: user-1 puts a rolling-update policy on the deployment

Then

- the call is rejected
  - rejected: NotEnoughPermission

