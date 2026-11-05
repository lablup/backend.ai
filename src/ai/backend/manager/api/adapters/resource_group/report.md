## resource_group

[background](/src/ai/backend/manager/api/adapters/resource_group/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/resource_group/adapter.py)

Scenario: incomplete 2 / 25

- built from ops (10)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_by_names: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - get_allowed_resource_groups_for_domain: representative success ✓ · representative rejection ✓
  - get_allowed_resource_groups_for_project: representative success ✓ · representative rejection ✓
  - lookup_name: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
- ops + direct implementation (1)
  - get_fair_share_spec: success present 2 · rejection present 2 (partial_bulk_get_ops, single_entity)
- direct implementation (14)
  - admin_replace_default_deployment_options: success present 2 · rejection present 2 (single_entity)
  - admin_replace_default_session_options: success present 1 · rejection present 2 (single_entity)
  - create: success present 2 · rejection present 3 (global_scope)
  - get_allowed_domains_for_resource_group: success present 2 · rejection present 1 (single_entity)
  - get_allowed_projects_for_resource_group: success present 1 · rejection present 1 (single_entity)
  - get_resource_info: success present 2 · rejection present 2 (single_entity)
  - purge: success present 2 · rejection present 2 (single_entity)
  - update: success present 5 · rejection present 3 (single_entity)
  - update_allowed_domains_for_resource_group: success present 1 · rejection present 3 (relation, single_entity)
  - update_allowed_projects_for_resource_group: success present 1 · rejection present 1 (relation, single_entity)
  - update_allowed_resource_groups_for_domain: success present 3 · rejection present 2 (global_scope, relation, single_entity)
  - update_allowed_resource_groups_for_project: success present 1 · rejection present 1 (global_scope, relation, single_entity)
  - update_config: success present 2 · rejection present 1 (single_entity)
  - update_fair_share_spec: success present 3 · rejection present 3 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [batch loading an empty id list answers an empty response without calling the lower layer](#reading-a-batch-load-of-no-ids-answers-an-empty-list) | answered |
| [when the superadmin batch loads two seeded groups and one unknown id, the items come back in the order requested and the item for the unknown id is empty](#reading-the-superadmin-batch-load-by-ids-leaves-a-missing-id-empty) | answered |
| [a user granted nothing batch loading two groups by id is not rejected as a call, and every item carries a denial for not enough permission](#reading-a-user-granted-nothing-batch-loading-by-ids-is-refused-per-item) | rejected |

**batch_load_by_names**

| scenario | verdict |
|---|---|
| [batch loading an empty name list answers an empty response without calling the lower layer](#reading-a-batch-load-of-no-names-answers-an-empty-list) | answered |
| [when the superadmin batch loads two seeded groups and one unknown name, the items come back in the order requested and the item for the unknown name is empty](#reading-the-superadmin-batch-load-by-names-leaves-a-missing-name-empty) | answered |
| [a user granted nothing batch loading two groups by name is not rejected as a call, and every item carries a denial for not enough permission](#reading-a-user-granted-nothing-batch-loading-by-names-is-refused-per-item) | rejected |

**get**

| scenario | verdict |
|---|---|
| [a user granted read through the role granted on the resource group reading it by name gets the whole group. the resource group is its own scope, so the role granted on it applies](#reading-a-user-granted-read-on-the-group-reads-it-by-name) | answered |
| [one resource group exists and the superadmin reads it by name, so the whole group comes back](#reading-the-superadmin-reads-a-resource-group-by-name) | answered |
| [a user granted nothing reading by name is rejected for not enough permission](#reading-a-user-granted-nothing-may-not-read-a-resource-group) | rejected |
| [a user granted nothing reading a name nothing answers to is rejected because no target answers to it, not for not enough permission. the step that looks up the id by name checks authentication alone and the permission check follows the lookup](#reading-a-user-granted-nothing-reading-a-name-nothing-answers-to-is-not-found-too) | rejected |
| [when the superadmin reads a name nothing answers to, the call is rejected because no target answers to it](#reading-the-superadmin-reading-a-name-nothing-answers-to-is-not-found) | rejected |

**get_allowed_resource_groups_for_domain**

| scenario | verdict |
|---|---|
| [a user granted the resource group read role in the domain scope reading the allow list of that domain gets only the linked group name](#allowing-a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it) | answered |
| [when one resource group is linked to a domain and one is not, reading the allow list of that domain as the superadmin answers only the linked group name](#allowing-the-superadmin-reads-the-groups-allowed-for-a-domain) | answered |
| [a user granted nothing trying to read the allow list of their own domain is rejected for not enough permission](#allowing-a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain) | rejected |
| [reading the allow list of a domain name nothing answers to is rejected because no target answers to it](#allowing-reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found) | rejected |

**get_allowed_resource_groups_for_project**

| scenario | verdict |
|---|---|
| [when a resource group is linked to a project, reading the allow list of that project as the superadmin answers the linked group name](#allowing-the-superadmin-reads-the-groups-allowed-for-a-project) | answered |
| [a user granted nothing trying to read the allow list of a project is rejected for not enough permission. reading has to be allowed in all three scopes, the caller's domain, the project and the caller themself](#allowing-a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project) | rejected |

**lookup_name**

| scenario | verdict |
|---|---|
| [a user granted nothing can still look up a resource group by name. this call checks authentication alone, and the call receiving that id checks the permission](#looking_up-a-user-granted-nothing-still-looks-up-a-resource-group-by-name) | answered |
| [when the superadmin looks up a resource group by name, the id of that resource group comes back](#looking_up-the-superadmin-looks-up-a-resource-group-by-name) | answered |
| [looking up the id of a name no resource group holds is rejected as no such target](#looking_up-looking-up-a-resource-group-name-nothing-answers-to-is-not-found) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to purge several resource groups at once gets none purged and every one in the failed list for not enough permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-resource-groups) | answered |
| [when the superadmin purges two resource groups and one unknown id at once, the two come back as deleted and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-resource-groups-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to edit several resource groups at once gets none edited and every one in the failed list for not enough permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-resource-groups) | answered |
| [when the superadmin changes the description of several resource groups at once, they all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-resource-groups-at-once) | answered |

**scoped_search**

| scenario | verdict |
|---|---|
| [a user granted the resource group read role in the domain scope searching that domain scope gets only the resource group linked to the domain, and the unlinked resource group does not come back](#searching-a-user-granted-read-in-the-domain-searches-the-groups-linked-to-it) | answered |
| [the superadmin searching a domain scope gets only the one resource group linked to that domain](#searching-the-superadmin-searching-a-domain-scope-sees-only-the-groups-linked-to-it) | answered |
| [a user granted nothing searching their own domain scope is rejected for not enough permission](#searching-a-user-granted-nothing-may-not-search-a-domain-scope) | rejected |

**search**

| scenario | verdict |
|---|---|
| [searching with the name of one of two resource groups as the filter answers only that group](#searching-a-name-filter-narrows-the-answer-to-that-resource-group) | answered |
| [when active and inactive groups are mixed, searching with the active filter answers only the active ones](#searching-an-active-filter-leaves-only-the-active-resource-groups) | answered |
| [when two resource groups exist and only the first item is asked for, one item comes back and the response says there is a next page](#searching-asking-for-the-first-resource-group-only-says-there-is-a-next-page) | answered |
| [the monitor searching without a filter gets the same response as the superadmin](#searching-the-monitor-searches-resource-groups-like-the-superadmin) | answered |
| [when two resource groups exist and the superadmin searches without a filter, both come back](#searching-the-superadmin-counts-every-resource-group-laid) | answered |
| [when a user who is not the superadmin searches every resource group without a filter, the call is rejected for lacking the role](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-resource-group) | rejected |

**get_fair_share_spec**

| scenario | verdict |
|---|---|
| [a user granted read through the role granted on the resource group reading the fair share config of a resource group with no agent gets the defaults set in the code and an empty weight list](#fair_share-a-user-granted-read-on-the-group-reads-its-fair-share-spec) | answered |
| [when the superadmin reads the fair share config of a resource group with no agent, the defaults set in the code come back and the weight list is empty](#fair_share-the-superadmin-reads-the-default-fair-share-spec) | answered |
| [a user granted nothing trying to read the fair share config is rejected for not enough permission](#fair_share-a-user-granted-nothing-may-not-read-the-fair-share-spec) | rejected |
| [when the superadmin reads the fair share config of a name nothing answers to, the call is rejected because no target answers to it](#fair_share-reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found) | rejected |

**admin_replace_default_deployment_options**

| scenario | verdict |
|---|---|
| [a user granted update through the role granted on the resource group replacing the default deployment options gets the options given whole](#options-a-user-granted-update-on-the-group-replaces-the-default-deployment-options) | answered |
| [when the superadmin replaces the default deployment options with the settings of one registered handler, the options given come back whole](#options-the-superadmin-replaces-the-default-deployment-options-whole) | answered |
| [a user granted nothing trying to replace the default deployment options is rejected for not enough permission](#options-a-user-granted-nothing-may-not-replace-the-default-deployment-options) | rejected |
| [replacing the options with the name of an unregistered deployment handler is rejected as invalid input](#options-naming-an-unregistered-deployment-handler-is-refused) | rejected |

**admin_replace_default_session_options**

| scenario | verdict |
|---|---|
| [when the superadmin replaces the default session options with a priority and the settings of one registered handler, the options given come back whole and the entries left out take the defaults in the code](#options-the-superadmin-replaces-the-default-session-options-whole) | answered |
| [a user granted nothing trying to replace the default session options is rejected for not enough permission](#options-a-user-granted-nothing-may-not-replace-the-default-session-options) | rejected |
| [replacing the options with the name of an unregistered session handler is rejected as invalid input](#options-naming-an-unregistered-session-handler-is-refused) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when no default group exists and the superadmin creates one designated as the default, the group comes back as the default](#creating-a-resource-group-made-as-the-default-answers-default) | answered |
| [when the superadmin creates a resource group with only a name, the whole group comes back active, public and not the default, filled from the defaults in the code](#creating-the-superadmin-makes-a-resource-group) | answered |
| [creating with a name another resource group already holds is rejected as a duplicate name](#creating-a-name-another-resource-group-already-holds-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a resource group, the call is rejected for lacking the role](#creating-a-user-who-is-not-the-superadmin-may-not-make-a-resource-group) | rejected |
| [when the monitor tries to create a resource group, the call is rejected for lacking the role. the monitor passes reads only](#creating-the-monitor-may-not-make-a-resource-group) | rejected |

**get_allowed_domains_for_resource_group**

| scenario | verdict |
|---|---|
| [a user granted read through the role granted on the resource group reading the allowed domains of the group gets an empty list because no domain is linked](#allowing-a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it) | answered |
| [when the superadmin reads the allowed domains of a resource group linked to a domain, that domain name comes back](#allowing-the-superadmin-reads-the-domains-allowed-for-a-resource-group) | answered |
| [a user granted nothing trying to read the allowed domains of a resource group is rejected for not enough permission](#allowing-a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group) | rejected |

**get_allowed_projects_for_resource_group**

| scenario | verdict |
|---|---|
| [when the superadmin reads the allowed projects of a resource group linked to a project, that project id comes back](#allowing-the-superadmin-reads-the-projects-allowed-for-a-resource-group) | answered |
| [a user granted nothing trying to read the allowed projects of a resource group is rejected for not enough permission](#allowing-a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group) | rejected |

**get_resource_info**

| scenario | verdict |
|---|---|
| [a user granted read through the role granted on the resource group reading the resource info gets the same response as the superadmin](#reading-a-user-granted-read-on-the-group-reads-its-resource-info) | answered |
| [when the superadmin reads the resource info of a group without agents, capacity, used and free are all empty](#reading-the-superadmin-reads-an-empty-resource-info-of-a-group-without-agents) | answered |
| [a user granted nothing reading the resource info is rejected for not enough permission](#reading-a-user-granted-nothing-may-not-read-the-resource-info) | rejected |
| [when the superadmin reads the resource info of a name nothing answers to, the call is rejected because no target answers to it](#reading-the-resource-info-of-a-name-nothing-answers-to-is-not-found) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [a user granted hard delete through the role granted on the resource group purging it gets the whole deleted group](#retiring-a-user-granted-hard-delete-on-the-group-purges-it) | answered |
| [one resource group exists and the superadmin purges it, so the whole deleted group comes back](#retiring-the-superadmin-purges-a-resource-group) | answered |
| [a user granted nothing trying to purge is rejected for not enough permission](#retiring-a-user-granted-nothing-may-not-purge-a-resource-group) | rejected |
| [when the superadmin purges a name nothing answers to, the call is rejected because no target answers to it](#retiring-the-superadmin-purging-a-name-nothing-answers-to-is-not-found) | rejected |

**update**

| scenario | verdict |
|---|---|
| [a user granted update through the role granted on the resource group changing the description gets the group with the new description](#editing-a-user-granted-update-on-the-group-changes-its-description) | answered |
| [an edit naming no field answers the group with nothing changed](#editing-an-edit-naming-no-field-changes-nothing) | answered |
| [deactivating an active group answers the group as inactive](#editing-deactivating-a-resource-group-answers-it-inactive) | answered |
| [when no default group exists, making a group the default answers it as the default](#editing-making-a-resource-group-the-default-answers-it-default) | answered |
| [when the superadmin changes only the description, the whole group comes back with the new description and the rest unchanged](#editing-the-superadmin-changing-the-description-leaves-the-rest) | answered |
| [a user granted nothing trying to change the description is rejected for not enough permission](#editing-a-user-granted-nothing-may-not-edit-a-resource-group) | rejected |
| [when another default group exists, making a different group the default is rejected because a default group already exists](#editing-making-a-second-resource-group-the-default-is-refused) | rejected |
| [when the superadmin edits a name nothing answers to, the call is rejected because no target answers to it](#editing-the-superadmin-editing-a-name-nothing-answers-to-is-not-found) | rejected |

**update_allowed_domains_for_resource_group**

| scenario | verdict |
|---|---|
| [when the superadmin adds a domain to the allowed domains of a resource group, the list holding that domain name comes back](#allowing-the-superadmin-allows-a-domain-for-a-resource-group) | answered |
| [a user granted nothing trying to add a domain to the allowed domains of a resource group is rejected for not enough permission. the step that writes the relation checks the permission of both scopes](#allowing-a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group) | rejected |
| [adding a domain name nothing answers to to the allowed domains of a resource group is rejected because no target answers to it](#allowing-allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found) | rejected |
| [removing a domain name nothing answers to from the allowed domains of a resource group is rejected because no target answers to it instead of being skipped. removing an unknown resource group name on the domain side is skipped](#allowing-disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found) | rejected |

**update_allowed_projects_for_resource_group**

| scenario | verdict |
|---|---|
| [when the superadmin adds a project to the allowed projects of a resource group, the list holding that project id comes back](#allowing-the-superadmin-allows-a-project-for-a-resource-group) | answered |
| [a user granted nothing trying to add a project to the allowed projects of a resource group is rejected for not enough permission](#allowing-a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group) | rejected |

**update_allowed_resource_groups_for_domain**

| scenario | verdict |
|---|---|
| [removing a resource group name nothing answers to from the allow list of a domain skips that name and an empty list comes back](#allowing-disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped) | answered |
| [when the superadmin adds a resource group to the allow list of a domain, the list holding that group name comes back](#allowing-the-superadmin-allows-a-resource-group-for-a-domain) | answered |
| [when the superadmin removes the resource group linked to a domain from the allow list, an empty list comes back](#allowing-the-superadmin-disallows-a-resource-group-for-a-domain) | answered |
| [when a user who is not the superadmin tries to add a resource group to the allow list of a domain, the call is rejected for lacking the role. the step that turns the resource group name into an id goes through the superadmin check](#allowing-a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain) | rejected |
| [adding a resource group name nothing answers to to the allow list of a domain is rejected because no target answers to it](#allowing-allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found) | rejected |

**update_allowed_resource_groups_for_project**

| scenario | verdict |
|---|---|
| [when the superadmin adds a resource group to the allow list of a project, the list holding that group name comes back](#allowing-the-superadmin-allows-a-resource-group-for-a-project) | answered |
| [when a user who is not the superadmin tries to add a resource group to the allow list of a project, the call is rejected for lacking the role](#allowing-a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project) | rejected |

**update_config**

| scenario | verdict |
|---|---|
| [when the superadmin changes the preemption config, the whole group comes back with the new preemption values](#editing-the-superadmin-changes-the-preemption-config) | answered |
| [when the superadmin changes the config to a last-in-first-out scheduler, private visibility, host network and a given proxy address, the whole group comes back with those values](#editing-the-superadmin-changes-the-scheduler-visibility-and-network-config) | answered |
| [a user granted nothing trying to change the config is rejected for not enough permission](#editing-a-user-granted-nothing-may-not-edit-the-config) | rejected |

**update_fair_share_spec**

| scenario | verdict |
|---|---|
| [when a user granted update in the group scope assigns a weight to one resource type, the whole group comes back. the returned node does not carry this config](#fair_share-a-user-granted-update-assigns-a-resource-weight) | answered |
| [a user granted update through the role granted on the resource group changing the half-life gets the whole group](#fair_share-a-user-granted-update-on-the-group-changes-its-fair-share-spec) | answered |
| [when the superadmin changes the half-life, the whole group comes back. the returned node does not carry this config](#fair_share-the-superadmin-changes-the-fair-share-half-life) | answered |
| [a user granted nothing trying to change the half-life is rejected for not enough permission](#fair_share-a-user-granted-nothing-may-not-change-the-fair-share-spec) | rejected |
| [assigning a weight to a resource type no agent reports is rejected as an invalid input](#fair_share-a-weight-on-a-resource-no-agent-reports-is-rejected) | rejected |
| [when the superadmin changes the half-life of a name nothing answers to, the call is rejected because no target answers to it](#fair_share-changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

batch loading an empty id list answers an empty response without calling the lower layer

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_ids: user-1 batch loads an empty id list

Then

- an empty response comes back
  - items = []

<a id="reading-the-superadmin-batch-load-by-ids-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-by-ids-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

when the superadmin batch loads two seeded groups and one unknown id, the items come back in the order requested and the item for the unknown id is empty

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_ids: user-1 batch loads 2 seeded resource groups and one unknown id

Then

- the items come back in the order requested and the item for a missing one is empty
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].name = 'wanted-1'
  - items[0].status.is_active = True
  - items[0].status.is_public = True
  - items[0].status.is_default = False
  - items[0].metadata.description = None
  - items[0].metadata.created_at: the time this run wrote
  - items[0].network.wsproxy_addr = None
  - items[0].network.use_host_network = False
  - items[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[0].scheduler.preemption.enabled = False
  - items[0].scheduler.preemption.preemptible_priority = 5
  - items[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[0].scheduler.preemption.preemption_min_runtime = 0.0
  - items[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[0].default_deployment_options: skipped: the default the installation sets
  - items[0].default_session_options: skipped: the default the installation sets
  - items[1].id: skipped: the database generates it
  - items[1].name = 'other-1'
  - items[1].status.is_active = True
  - items[1].status.is_public = True
  - items[1].status.is_default = False
  - items[1].metadata.description = None
  - items[1].metadata.created_at: the time this run wrote
  - items[1].network.wsproxy_addr = None
  - items[1].network.use_host_network = False
  - items[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[1].scheduler.preemption.enabled = False
  - items[1].scheduler.preemption.preemptible_priority = 5
  - items[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[1].scheduler.preemption.preemption_min_runtime = 0.0
  - items[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[1].default_deployment_options: skipped: the default the installation sets
  - items[1].default_session_options: skipped: the default the installation sets
  - items[2] = None

<a id="reading-a-user-granted-nothing-batch-loading-by-ids-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-by-ids-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted nothing batch loading two groups by id is not rejected as a call, and every item carries a denial for not enough permission

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_ids: user-1 batch loads the 2 seeded resource groups by id

Then

- every item carries a denial for not enough permission
  - len(items) = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_by_names

<a id="reading-a-batch-load-of-no-names-answers-an-empty-list"></a>

#### [a-batch-load-of-no-names-answers-an-empty-list](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

batch loading an empty name list answers an empty response without calling the lower layer

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_names: user-1 batch loads an empty name list

Then

- an empty response comes back
  - items = []

<a id="reading-the-superadmin-batch-load-by-names-leaves-a-missing-name-empty"></a>

#### [the-superadmin-batch-load-by-names-leaves-a-missing-name-empty](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

when the superadmin batch loads two seeded groups and one unknown name, the items come back in the order requested and the item for the unknown name is empty

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_names: user-1 batch loads 2 seeded resource groups and one unknown name

Then

- the items come back in the order requested and the item for a missing one is empty
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].name = 'wanted-1'
  - items[0].status.is_active = True
  - items[0].status.is_public = True
  - items[0].status.is_default = False
  - items[0].metadata.description = None
  - items[0].metadata.created_at: the time this run wrote
  - items[0].network.wsproxy_addr = None
  - items[0].network.use_host_network = False
  - items[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[0].scheduler.preemption.enabled = False
  - items[0].scheduler.preemption.preemptible_priority = 5
  - items[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[0].scheduler.preemption.preemption_min_runtime = 0.0
  - items[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[0].default_deployment_options: skipped: the default the installation sets
  - items[0].default_session_options: skipped: the default the installation sets
  - items[1].id: skipped: the database generates it
  - items[1].name = 'other-1'
  - items[1].status.is_active = True
  - items[1].status.is_public = True
  - items[1].status.is_default = False
  - items[1].metadata.description = None
  - items[1].metadata.created_at: the time this run wrote
  - items[1].network.wsproxy_addr = None
  - items[1].network.use_host_network = False
  - items[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - items[1].scheduler.preemption.enabled = False
  - items[1].scheduler.preemption.preemptible_priority = 5
  - items[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - items[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - items[1].scheduler.preemption.preemption_min_runtime = 0.0
  - items[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - items[1].default_deployment_options: skipped: the default the installation sets
  - items[1].default_session_options: skipped: the default the installation sets
  - items[2] = None

<a id="reading-a-user-granted-nothing-batch-loading-by-names-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-by-names-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted nothing batch loading two groups by name is not rejected as a call, and every item carries a denial for not enough permission

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.batch_load_by_names: user-1 batch loads the 2 seeded resource groups by name

Then

- every item carries a denial for not enough permission
  - len(items) = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-on-the-group-reads-it-by-name"></a>

#### [a-user-granted-read-on-the-group-reads-it-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted read through the role granted on the resource group reading it by name gets the whole group. the resource group is its own scope, so the role granted on it applies

Given

- one resource group and one regular user granted the READ role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.get: user-1 reads resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="reading-the-superadmin-reads-a-resource-group-by-name"></a>

#### [the-superadmin-reads-a-resource-group-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

one resource group exists and the superadmin reads it by name, so the whole group comes back

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get: user-1 reads resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="reading-a-user-granted-nothing-may-not-read-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-read-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted nothing reading by name is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get: user-1 reads resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-a-user-granted-nothing-reading-a-name-nothing-answers-to-is-not-found-too"></a>

#### [a-user-granted-nothing-reading-a-name-nothing-answers-to-is-not-found-too](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted nothing reading a name nothing answers to is rejected because no target answers to it, not for not enough permission. the step that looks up the id by name checks authentication alone and the permission check follows the lookup

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get: user-1 reads a name that does not exist

Then

- the call is rejected
  - rejected: ResourceGroupNotFound

<a id="reading-the-superadmin-reading-a-name-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

when the superadmin reads a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get: user-1 reads a name that does not exist

Then

- the call is rejected
  - rejected: ResourceGroupNotFound

### get_allowed_resource_groups_for_domain

<a id="allowing-a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it"></a>

#### [a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted the resource group read role in the domain scope reading the allow list of that domain gets only the linked group name

Given

- one domain, one resource group linked to the domain and one not linked, and one regular user granted the resource group read role in the domain scope
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the resource group read role in the domain scope
    - Role group-reader-1: applies only within the scope it is granted in
    - Role group-reader-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-reader-1

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain: user-1 reads the allow list of domain home-1

Then

- the allow list holds only the name of the linked resource group
  - items = ['linked-1']

<a id="allowing-the-superadmin-reads-the-groups-allowed-for-a-domain"></a>

#### [the-superadmin-reads-the-groups-allowed-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when one resource group is linked to a domain and one is not, reading the allow list of that domain as the superadmin answers only the linked group name

Given

- one domain, one resource group linked to the domain and one not linked, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain: user-1 reads the allow list of domain home-1

Then

- the allow list holds only the name of the linked resource group
  - items = ['linked-1']

<a id="allowing-a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain"></a>

#### [a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to read the allow list of their own domain is rejected for not enough permission

Given

- one domain, one resource group linked to the domain and one not linked, and one regular user
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain: user-1 reads the allow list of domain home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="allowing-reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found"></a>

#### [reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

reading the allow list of a domain name nothing answers to is rejected because no target answers to it

Given

- one domain, one resource group linked to the domain and one not linked, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_domain: user-1 reads the allow list of a domain that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get_allowed_resource_groups_for_project

<a id="allowing-the-superadmin-reads-the-groups-allowed-for-a-project"></a>

#### [the-superadmin-reads-the-groups-allowed-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when a resource group is linked to a project, reading the allow list of that project as the superadmin answers the linked group name

Given

- one project, one resource group linked to the project and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_project: user-1 reads the allow list of project team-1

Then

- the allow list holds only the name of the linked resource group
  - items = ['resource-group-1']

<a id="allowing-a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project"></a>

#### [a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to read the allow list of a project is rejected for not enough permission. reading has to be allowed in all three scopes, the caller's domain, the project and the caller themself

Given

- one project, one resource group linked to the project and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_resource_groups_for_project: user-1 reads the allow list of project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### lookup_name

<a id="looking_up-a-user-granted-nothing-still-looks-up-a-resource-group-by-name"></a>

#### [a-user-granted-nothing-still-looks-up-a-resource-group-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_looking_up.py): pass

a user granted nothing can still look up a resource group by name. this call checks authentication alone, and the call receiving that id checks the permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.lookup_name: user-1 looks up the id of resource-group-1

Then

- the id of that resource group comes back
  - id: same as the id of the resource group seeded in advance

<a id="looking_up-the-superadmin-looks-up-a-resource-group-by-name"></a>

#### [the-superadmin-looks-up-a-resource-group-by-name](/tests/scenario/bai_scenario/manager/resource_group/test_looking_up.py): pass

when the superadmin looks up a resource group by name, the id of that resource group comes back

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.lookup_name: user-1 looks up the id of resource-group-1

Then

- the id of that resource group comes back
  - id: same as the id of the resource group seeded in advance

<a id="looking_up-looking-up-a-resource-group-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-resource-group-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_looking_up.py): pass

looking up the id of a name no resource group holds is rejected as no such target

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.lookup_name: user-1 looks up the id of no-such-group

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-resource-groups"></a>

#### [a-user-granted-nothing-purges-none-of-several-resource-groups](/tests/scenario/bai_scenario/manager/resource_group/test_partial_bulk_purging.py): pass

a user granted nothing trying to purge several resource groups at once gets none purged and every one in the failed list for not enough permission

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.partial_bulk_purge: user-1 purges 2 resource groups at once

Then

- no group is processed and every group comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the group
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the group
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-resource-groups-answers-for-the-missing-one"></a>

#### [purging-several-resource-groups-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_group/test_partial_bulk_purging.py): pass

when the superadmin purges two resource groups and one unknown id at once, the two come back as deleted and the unknown id comes back in the failed list because no target answers to it

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.partial_bulk_purge: user-1 purges 2 resource groups and one unknown id at once

Then

- every group comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].status.is_active = True
  - successes[0].status.is_public = True
  - successes[0].status.is_default = False
  - successes[0].metadata.description = None
  - successes[0].metadata.created_at: the time this run wrote
  - successes[0].network.wsproxy_addr = None
  - successes[0].network.use_host_network = False
  - successes[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - successes[0].scheduler.preemption.enabled = False
  - successes[0].scheduler.preemption.preemptible_priority = 5
  - successes[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - successes[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - successes[0].scheduler.preemption.preemption_min_runtime = 0.0
  - successes[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - successes[0].default_deployment_options: skipped: the default the installation sets
  - successes[0].default_session_options: skipped: the default the installation sets
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].status.is_active = True
  - successes[1].status.is_public = True
  - successes[1].status.is_default = False
  - successes[1].metadata.description = None
  - successes[1].metadata.created_at: the time this run wrote
  - successes[1].network.wsproxy_addr = None
  - successes[1].network.use_host_network = False
  - successes[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - successes[1].scheduler.preemption.enabled = False
  - successes[1].scheduler.preemption.preemptible_priority = 5
  - successes[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - successes[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - successes[1].scheduler.preemption.preemption_min_runtime = 0.0
  - successes[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - successes[1].default_deployment_options: skipped: the default the installation sets
  - successes[1].default_session_options: skipped: the default the installation sets
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-resource-groups"></a>

#### [a-user-granted-nothing-edits-none-of-several-resource-groups](/tests/scenario/bai_scenario/manager/resource_group/test_partial_bulk_editing.py): pass

a user granted nothing trying to edit several resource groups at once gets none edited and every one in the failed list for not enough permission

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.partial_bulk_update: user-1 edits the description of 2 resource groups at once

Then

- no group is processed and every group comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the group
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the group
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-resource-groups-at-once"></a>

#### [the-superadmin-edits-several-resource-groups-at-once](/tests/scenario/bai_scenario/manager/resource_group/test_partial_bulk_editing.py): pass

when the superadmin changes the description of several resource groups at once, they all come back with the new description and nothing failed

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.partial_bulk_update: user-1 edits the description of 2 resource groups at once

Then

- every group comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].status.is_active = True
  - successes[0].status.is_public = True
  - successes[0].status.is_default = False
  - successes[0].metadata.description = 'the description edited at once'
  - successes[0].metadata.created_at: the time this run wrote
  - successes[0].network.wsproxy_addr = None
  - successes[0].network.use_host_network = False
  - successes[0].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - successes[0].scheduler.preemption.enabled = False
  - successes[0].scheduler.preemption.preemptible_priority = 5
  - successes[0].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - successes[0].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - successes[0].scheduler.preemption.preemption_min_runtime = 0.0
  - successes[0].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - successes[0].default_deployment_options: skipped: the default the installation sets
  - successes[0].default_session_options: skipped: the default the installation sets
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].status.is_active = True
  - successes[1].status.is_public = True
  - successes[1].status.is_default = False
  - successes[1].metadata.description = 'the description edited at once'
  - successes[1].metadata.created_at: the time this run wrote
  - successes[1].network.wsproxy_addr = None
  - successes[1].network.use_host_network = False
  - successes[1].scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - successes[1].scheduler.preemption.enabled = False
  - successes[1].scheduler.preemption.preemptible_priority = 5
  - successes[1].scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - successes[1].scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - successes[1].scheduler.preemption.preemption_min_runtime = 0.0
  - successes[1].scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - successes[1].default_deployment_options: skipped: the default the installation sets
  - successes[1].default_session_options: skipped: the default the installation sets
  - failed = []

### scoped_search

<a id="searching-a-user-granted-read-in-the-domain-searches-the-groups-linked-to-it"></a>

#### [a-user-granted-read-in-the-domain-searches-the-groups-linked-to-it](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

a user granted the resource group read role in the domain scope searching that domain scope gets only the resource group linked to the domain, and the unlinked resource group does not come back

Given

- one domain, one resource group linked to the domain and one not linked, and one regular user granted the resource group read role in the domain scope
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the resource group read role in the domain scope
    - Role group-reader-1: applies only within the scope it is granted in
    - Role group-reader-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-reader-1

When

- ResourceGroupAdapter.scoped_search: user-1 searches the domain home-1 scope

Then

- only the one resource group linked to the domain comes back
  - items = ['linked-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-searching-a-domain-scope-sees-only-the-groups-linked-to-it"></a>

#### [the-superadmin-searching-a-domain-scope-sees-only-the-groups-linked-to-it](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

the superadmin searching a domain scope gets only the one resource group linked to that domain

Given

- one domain, one resource group linked to the domain and one not linked, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.scoped_search: user-1 searches the domain home-1 scope

Then

- only the one resource group linked to the domain comes back
  - items = ['linked-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-a-domain-scope"></a>

#### [a-user-granted-nothing-may-not-search-a-domain-scope](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

a user granted nothing searching their own domain scope is rejected for not enough permission

Given

- one domain, one resource group linked to the domain and one not linked, and one regular user
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.scoped_search: user-1 searches the domain home-1 scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search

<a id="searching-a-name-filter-narrows-the-answer-to-that-resource-group"></a>

#### [a-name-filter-narrows-the-answer-to-that-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

searching with the name of one of two resource groups as the filter answers only that group

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 searches with the name wanted-1 filter

Then

- only the one resource group the filter names comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-an-active-filter-leaves-only-the-active-resource-groups"></a>

#### [an-active-filter-leaves-only-the-active-resource-groups](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

when active and inactive groups are mixed, searching with the active filter answers only the active ones

Given

- one active resource group, one inactive group and one superadmin
  - Domain home-1
  - Resource group active-1: uses the fifo scheduler
  - Resource group inactive-1: uses the fifo scheduler, inactive
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 searches with the active filter

Then

- only the resource groups that must appear in the response come back
  - items = ['active-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-asking-for-the-first-resource-group-only-says-there-is-a-next-page"></a>

#### [asking-for-the-first-resource-group-only-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

when two resource groups exist and only the first item is asked for, one item comes back and the response says there is a next page

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 asks for one item from the front

Then

- the first page holding one item comes back
  - len(items) = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-the-monitor-searches-resource-groups-like-the-superadmin"></a>

#### [the-monitor-searches-resource-groups-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

the monitor searching without a filter gets the same response as the superadmin

Given

- two resource groups and one monitor
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 searches every resource group without a filter

Then

- only the resource groups that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-counts-every-resource-group-laid"></a>

#### [the-superadmin-counts-every-resource-group-laid](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

when two resource groups exist and the superadmin searches without a filter, both come back

Given

- two resource groups and one superadmin
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 searches every resource group without a filter

Then

- only the resource groups that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-resource-group"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_searching.py): pass

when a user who is not the superadmin searches every resource group without a filter, the call is rejected for lacking the role

Given

- two resource groups and one regular user
  - Domain home-1
  - Resource group wanted-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.search: user-1 searches every resource group without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get_fair_share_spec

<a id="fair_share-a-user-granted-read-on-the-group-reads-its-fair-share-spec"></a>

#### [a-user-granted-read-on-the-group-reads-its-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

a user granted read through the role granted on the resource group reading the fair share config of a resource group with no agent gets the defaults set in the code and an empty weight list

Given

- one resource group and one regular user granted the READ role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.get_fair_share_spec: user-1 reads the fair share config of resource-group-1

Then

- the default fair share settings come back and the weight list is empty
  - half_life_days = 7
  - lookback_days = 28
  - decay_unit_days = 1
  - default_weight = '1.0'
  - resource_weights = []

<a id="fair_share-the-superadmin-reads-the-default-fair-share-spec"></a>

#### [the-superadmin-reads-the-default-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

when the superadmin reads the fair share config of a resource group with no agent, the defaults set in the code come back and the weight list is empty

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_fair_share_spec: user-1 reads the fair share config of resource-group-1

Then

- the default fair share settings come back and the weight list is empty
  - half_life_days = 7
  - lookback_days = 28
  - decay_unit_days = 1
  - default_weight = '1.0'
  - resource_weights = []

<a id="fair_share-a-user-granted-nothing-may-not-read-the-fair-share-spec"></a>

#### [a-user-granted-nothing-may-not-read-the-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

a user granted nothing trying to read the fair share config is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_fair_share_spec: user-1 reads the fair share config of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="fair_share-reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"></a>

#### [reading-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

when the superadmin reads the fair share config of a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_fair_share_spec: user-1 reads the fair share config of a name that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_replace_default_deployment_options

<a id="options-a-user-granted-update-on-the-group-replaces-the-default-deployment-options"></a>

#### [a-user-granted-update-on-the-group-replaces-the-default-deployment-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

a user granted update through the role granted on the resource group replacing the default deployment options gets the options given whole

Given

- one resource group and one regular user granted the UPDATE role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.admin_replace_default_deployment_options: user-1 replaces the default deployment options of resource-group-1 with the selection policy STRICT and the settings of handler check-replica-deployments

Then

- only the replaced deployment options come back
  - resource_group_name = 'resource-group-1'
  - default_deployment_options.handler_options.default.timeout_sec = 600
  - default_deployment_options.handler_options.default.max_retry_count = 3
  - default_deployment_options.handler_options.by_handler = [('check-replica-deployments', 60, None)]
  - default_deployment_options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-the-superadmin-replaces-the-default-deployment-options-whole"></a>

#### [the-superadmin-replaces-the-default-deployment-options-whole](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

when the superadmin replaces the default deployment options with the settings of one registered handler, the options given come back whole

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_deployment_options: user-1 replaces the default deployment options of resource-group-1 with the selection policy STRICT and the settings of handler check-replica-deployments

Then

- only the replaced deployment options come back
  - resource_group_name = 'resource-group-1'
  - default_deployment_options.handler_options.default.timeout_sec = 600
  - default_deployment_options.handler_options.default.max_retry_count = 3
  - default_deployment_options.handler_options.by_handler = [('check-replica-deployments', 60, None)]
  - default_deployment_options.agent_selection_policy = <AgentSelectionPolicyEnum.STRICT: 'strict'>

<a id="options-a-user-granted-nothing-may-not-replace-the-default-deployment-options"></a>

#### [a-user-granted-nothing-may-not-replace-the-default-deployment-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

a user granted nothing trying to replace the default deployment options is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_deployment_options: user-1 replaces the default deployment options of resource-group-1 with the selection policy STRICT and the settings of handler check-replica-deployments

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="options-naming-an-unregistered-deployment-handler-is-refused"></a>

#### [naming-an-unregistered-deployment-handler-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

replacing the options with the name of an unregistered deployment handler is rejected as invalid input

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_deployment_options: user-1 replaces the default deployment options of resource-group-1 with the selection policy STRICT and the settings of handler no-such-handler

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### admin_replace_default_session_options

<a id="options-the-superadmin-replaces-the-default-session-options-whole"></a>

#### [the-superadmin-replaces-the-default-session-options-whole](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

when the superadmin replaces the default session options with a priority and the settings of one registered handler, the options given come back whole and the entries left out take the defaults in the code

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_session_options: user-1 replaces the default session options of resource-group-1 with a priority and the settings of handler terminate-sessions

Then

- only the replaced session options come back
  - resource_group_name = 'resource-group-1'
  - default_session_options.priority = 20
  - default_session_options.is_preemptible = True
  - default_session_options.cluster_mode = <ClusterModeEnum.SINGLE_NODE: 'single-node'>
  - default_session_options.default_failure_policy = <FailurePolicyEnum.STRICT: 'strict'>
  - default_session_options.default_kernel_execution_spec = None
  - default_session_options.handler_options.default.timeout_sec = 600
  - default_session_options.handler_options.default.max_retry_count = 3
  - default_session_options.handler_options.by_handler = [('terminate-sessions', 60, None)]
  - default_session_options.agent_selection_policy = <AgentSelectionPolicyEnum.PREFERRED: 'preferred'>

<a id="options-a-user-granted-nothing-may-not-replace-the-default-session-options"></a>

#### [a-user-granted-nothing-may-not-replace-the-default-session-options](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

a user granted nothing trying to replace the default session options is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_session_options: user-1 replaces the default session options of resource-group-1 with a priority and the settings of handler terminate-sessions

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="options-naming-an-unregistered-session-handler-is-refused"></a>

#### [naming-an-unregistered-session-handler-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_options.py): pass

replacing the options with the name of an unregistered session handler is rejected as invalid input

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.admin_replace_default_session_options: user-1 replaces the default session options of resource-group-1 with a priority and the settings of handler no-such-handler

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### create

<a id="creating-a-resource-group-made-as-the-default-answers-default"></a>

#### [a-resource-group-made-as-the-default-answers-default](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py): pass

when no default group exists and the superadmin creates one designated as the default, the group comes back as the default

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.create: user-1 creates primary as the default group

Then

- the whole resource group just created comes back
  - id: skipped: the database generates it
  - name = 'primary'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = True
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="creating-the-superadmin-makes-a-resource-group"></a>

#### [the-superadmin-makes-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py): pass

when the superadmin creates a resource group with only a name, the whole group comes back active, public and not the default, filled from the defaults in the code

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.create: user-1 creates compute

Then

- the whole resource group just created comes back
  - id: skipped: the database generates it
  - name = 'compute'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="creating-a-name-another-resource-group-already-holds-is-refused"></a>

#### [a-name-another-resource-group-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py): pass

creating with a name another resource group already holds is rejected as a duplicate name

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.create: user-1 creates resource-group-1

Then

- the call is rejected
  - rejected: ResourceGroupConflict

<a id="creating-a-user-who-is-not-the-superadmin-may-not-make-a-resource-group"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py): pass

when a user who is not the superadmin tries to create a resource group, the call is rejected for lacking the role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.create: user-1 creates by-a-user

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-the-monitor-may-not-make-a-resource-group"></a>

#### [the-monitor-may-not-make-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_creating.py): pass

when the monitor tries to create a resource group, the call is rejected for lacking the role. the monitor passes reads only

Given

- one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.create: user-1 creates by-the-monitor

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get_allowed_domains_for_resource_group

<a id="allowing-a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it"></a>

#### [a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted read through the role granted on the resource group reading the allowed domains of the group gets an empty list because no domain is linked

Given

- one resource group and one regular user granted the READ role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group: user-1 reads the allowed domains of resource-group-1

Then

- the allow list is empty
  - items = []

<a id="allowing-the-superadmin-reads-the-domains-allowed-for-a-resource-group"></a>

#### [the-superadmin-reads-the-domains-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin reads the allowed domains of a resource group linked to a domain, that domain name comes back

Given

- one domain, one resource group linked to the domain and one not linked, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group: user-1 reads the allowed domains of linked-1

Then

- the allowed domains hold only the name of the linked domain
  - items = ['home-1']

<a id="allowing-a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to read the allowed domains of a resource group is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_domains_for_resource_group: user-1 reads the allowed domains of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_allowed_projects_for_resource_group

<a id="allowing-the-superadmin-reads-the-projects-allowed-for-a-resource-group"></a>

#### [the-superadmin-reads-the-projects-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin reads the allowed projects of a resource group linked to a project, that project id comes back

Given

- one project, one resource group linked to the project and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_projects_for_resource_group: user-1 reads the allowed projects of resource-group-1

Then

- the allowed projects hold only the id of the linked project
  - items: same as the linked project

<a id="allowing-a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to read the allowed projects of a resource group is rejected for not enough permission

Given

- one project, one resource group linked to the project and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_allowed_projects_for_resource_group: user-1 reads the allowed projects of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_resource_info

<a id="reading-a-user-granted-read-on-the-group-reads-its-resource-info"></a>

#### [a-user-granted-read-on-the-group-reads-its-resource-info](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted read through the role granted on the resource group reading the resource info gets the same response as the superadmin

Given

- one resource group and one regular user granted the READ role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.get_resource_info: user-1 reads the resource info of resource-group-1

Then

- capacity, used and free are all empty
  - capacity.entries = []
  - used.entries = []
  - free.entries = []

<a id="reading-the-superadmin-reads-an-empty-resource-info-of-a-group-without-agents"></a>

#### [the-superadmin-reads-an-empty-resource-info-of-a-group-without-agents](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

when the superadmin reads the resource info of a group without agents, capacity, used and free are all empty

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_resource_info: user-1 reads the resource info of resource-group-1

Then

- capacity, used and free are all empty
  - capacity.entries = []
  - used.entries = []
  - free.entries = []

<a id="reading-a-user-granted-nothing-may-not-read-the-resource-info"></a>

#### [a-user-granted-nothing-may-not-read-the-resource-info](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

a user granted nothing reading the resource info is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_resource_info: user-1 reads the resource info of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-the-resource-info-of-a-name-nothing-answers-to-is-not-found"></a>

#### [the-resource-info-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_reading.py): pass

when the superadmin reads the resource info of a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.get_resource_info: user-1 reads the resource info of a name that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

### purge

<a id="retiring-a-user-granted-hard-delete-on-the-group-purges-it"></a>

#### [a-user-granted-hard-delete-on-the-group-purges-it](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py): pass

a user granted hard delete through the role granted on the resource group purging it gets the whole deleted group

Given

- one resource group and one regular user granted the HARD_DELETE role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the HARD_DELETE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: HARD_DELETE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.purge: user-1 purges resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="retiring-the-superadmin-purges-a-resource-group"></a>

#### [the-superadmin-purges-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py): pass

one resource group exists and the superadmin purges it, so the whole deleted group comes back

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.purge: user-1 purges resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="retiring-a-user-granted-nothing-may-not-purge-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-purge-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py): pass

a user granted nothing trying to purge is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.purge: user-1 purges resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-the-superadmin-purging-a-name-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-purging-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_retiring.py): pass

when the superadmin purges a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.purge: user-1 purges a name that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update

<a id="editing-a-user-granted-update-on-the-group-changes-its-description"></a>

#### [a-user-granted-update-on-the-group-changes-its-description](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

a user granted update through the role granted on the resource group changing the description gets the group with the new description

Given

- one resource group and one regular user granted the UPDATE role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, changing the description to a new value

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = 'moved to the second rack'
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-an-edit-naming-no-field-changes-nothing"></a>

#### [an-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

an edit naming no field answers the group with nothing changed

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1 naming no field

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-deactivating-a-resource-group-answers-it-inactive"></a>

#### [deactivating-a-resource-group-answers-it-inactive](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

deactivating an active group answers the group as inactive

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, setting active to False

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = False
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-making-a-resource-group-the-default-answers-it-default"></a>

#### [making-a-resource-group-the-default-answers-it-default](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when no default group exists, making a group the default answers it as the default

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, setting default to True

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = True
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-the-superadmin-changing-the-description-leaves-the-rest"></a>

#### [the-superadmin-changing-the-description-leaves-the-rest](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when the superadmin changes only the description, the whole group comes back with the new description and the rest unchanged

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, changing the description to a new value

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = 'moved to the second rack'
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-a-user-granted-nothing-may-not-edit-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-edit-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

a user granted nothing trying to change the description is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, changing the description to a new value

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-making-a-second-resource-group-the-default-is-refused"></a>

#### [making-a-second-resource-group-the-default-is-refused](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when another default group exists, making a different group the default is rejected because a default group already exists

Given

- one default resource group, one non-default group and one superadmin
  - Domain home-1
  - Resource group default-group-1: uses the fifo scheduler, default group
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates resource-group-1, setting default to True

Then

- the call is rejected
  - rejected: DefaultResourceGroupAlreadyExists

<a id="editing-the-superadmin-editing-a-name-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when the superadmin edits a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update: user-1 updates a name that does not exist, changing the description to a new value

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update_allowed_domains_for_resource_group

<a id="allowing-the-superadmin-allows-a-domain-for-a-resource-group"></a>

#### [the-superadmin-allows-a-domain-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin adds a domain to the allowed domains of a resource group, the list holding that domain name comes back

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group: user-1 adds home-1 in the allowed domains of other-1

Then

- the allowed domains hold only the name of the linked domain
  - items = ['home-1']

<a id="allowing-a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to add a domain to the allowed domains of a resource group is rejected for not enough permission. the step that writes the relation checks the permission of both scopes

Given

- one domain, two resource groups neither of which is linked to the domain, and one regular user
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group: user-1 adds home-1 in the allowed domains of other-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="allowing-allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"></a>

#### [allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

adding a domain name nothing answers to to the allowed domains of a resource group is rejected because no target answers to it

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group: user-1 adds an unknown domain name in the allowed domains of other-1

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="allowing-disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"></a>

#### [disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

removing a domain name nothing answers to from the allowed domains of a resource group is rejected because no target answers to it instead of being skipped. removing an unknown resource group name on the domain side is skipped

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_domains_for_resource_group: user-1 removes an unknown domain name in the allowed domains of other-1

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update_allowed_projects_for_resource_group

<a id="allowing-the-superadmin-allows-a-project-for-a-resource-group"></a>

#### [the-superadmin-allows-a-project-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin adds a project to the allowed projects of a resource group, the list holding that project id comes back

Given

- one project, one resource group and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_projects_for_resource_group: user-1 adds team-1 to the allowed projects of resource-group-1

Then

- the allowed projects hold only the id of the linked project
  - items: same as the linked project

<a id="allowing-a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group"></a>

#### [a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

a user granted nothing trying to add a project to the allowed projects of a resource group is rejected for not enough permission

Given

- one project, one resource group and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_projects_for_resource_group: user-1 adds team-1 to the allowed projects of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update_allowed_resource_groups_for_domain

<a id="allowing-disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped"></a>

#### [disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

removing a resource group name nothing answers to from the allow list of a domain skips that name and an empty list comes back

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain: user-1 removes an unknown resource group name in the allow list of domain home-1

Then

- the allow list is empty
  - items = []

<a id="allowing-the-superadmin-allows-a-resource-group-for-a-domain"></a>

#### [the-superadmin-allows-a-resource-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin adds a resource group to the allow list of a domain, the list holding that group name comes back

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain: user-1 adds other-1 in the allow list of domain home-1

Then

- the allow list holds only the name of the resource group just linked
  - items = ['other-1']

<a id="allowing-the-superadmin-disallows-a-resource-group-for-a-domain"></a>

#### [the-superadmin-disallows-a-resource-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin removes the resource group linked to a domain from the allow list, an empty list comes back

Given

- one domain, one resource group linked to the domain and one not linked, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Domain home-1 whose sessions can use Resource group linked-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain: user-1 removes linked-1 in the allow list of domain home-1

Then

- the allow list is empty
  - items = []

<a id="allowing-a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain"></a>

#### [a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when a user who is not the superadmin tries to add a resource group to the allow list of a domain, the call is rejected for lacking the role. the step that turns the resource group name into an id goes through the superadmin check

Given

- one domain, two resource groups neither of which is linked to the domain, and one regular user
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain: user-1 adds other-1 in the allow list of domain home-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="allowing-allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found"></a>

#### [allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

adding a resource group name nothing answers to to the allow list of a domain is rejected because no target answers to it

Given

- one domain, two resource groups neither of which is linked to the domain, and one superadmin
  - Domain home-1
  - Resource group linked-1: uses the fifo scheduler
  - Resource group other-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_domain: user-1 adds an unknown resource group name in the allow list of domain home-1

Then

- the call is rejected
  - rejected: ResourceGroupNotFound

### update_allowed_resource_groups_for_project

<a id="allowing-the-superadmin-allows-a-resource-group-for-a-project"></a>

#### [the-superadmin-allows-a-resource-group-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when the superadmin adds a resource group to the allow list of a project, the list holding that group name comes back

Given

- one project, one resource group and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_project: user-1 adds resource-group-1 to the allow list of project team-1

Then

- the allow list holds only the name of the linked resource group
  - items = ['resource-group-1']

<a id="allowing-a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project"></a>

#### [a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project](/tests/scenario/bai_scenario/manager/resource_group/test_allowing.py): pass

when a user who is not the superadmin tries to add a resource group to the allow list of a project, the call is rejected for lacking the role

Given

- one project, one resource group and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_allowed_resource_groups_for_project: user-1 adds resource-group-1 to the allow list of project team-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update_config

<a id="editing-the-superadmin-changes-the-preemption-config"></a>

#### [the-superadmin-changes-the-preemption-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when the superadmin changes the preemption config, the whole group comes back with the new preemption values

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_config: user-1 updates the preemption config of resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = True
  - scheduler.preemption.preemptible_priority = 3
  - scheduler.preemption.order = <PreemptionOrder.NEWEST: 'newest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.RESCHEDULE: 'reschedule'>
  - scheduler.preemption.preemption_min_runtime = 60.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.PROJECT: 'project'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-the-superadmin-changes-the-scheduler-visibility-and-network-config"></a>

#### [the-superadmin-changes-the-scheduler-visibility-and-network-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

when the superadmin changes the config to a last-in-first-out scheduler, private visibility, host network and a given proxy address, the whole group comes back with those values

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_config: user-1 updates the scheduler, visibility and network config of resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = False
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = 'https://proxy.example.test'
  - network.use_host_network = True
  - scheduler.type = <SchedulerTypeDTO.LIFO: 'lifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="editing-a-user-granted-nothing-may-not-edit-the-config"></a>

#### [a-user-granted-nothing-may-not-edit-the-config](/tests/scenario/bai_scenario/manager/resource_group/test_editing.py): pass

a user granted nothing trying to change the config is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_config: user-1 updates the scheduler, visibility and network config of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update_fair_share_spec

<a id="fair_share-a-user-granted-update-assigns-a-resource-weight"></a>

#### [a-user-granted-update-assigns-a-resource-weight](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

when a user granted update in the group scope assigns a weight to one resource type, the whole group comes back. the returned node does not carry this config

Given

- one resource group and one regular user granted the UPDATE role in the group scope. the group's agent reports one resource slot type with its capacity
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 0 in use
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 assigns a weight to slot-1 on resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="fair_share-a-user-granted-update-on-the-group-changes-its-fair-share-spec"></a>

#### [a-user-granted-update-on-the-group-changes-its-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

a user granted update through the role granted on the resource group changing the half-life gets the whole group

Given

- one resource group and one regular user granted the UPDATE role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 changes the half-life in the fair share config of resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="fair_share-the-superadmin-changes-the-fair-share-half-life"></a>

#### [the-superadmin-changes-the-fair-share-half-life](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

when the superadmin changes the half-life, the whole group comes back. the returned node does not carry this config

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 changes the half-life in the fair share config of resource-group-1

Then

- the whole resource group seeded in advance comes back
  - id: skipped: the database generates it
  - name = 'resource-group-1'
  - status.is_active = True
  - status.is_public = True
  - status.is_default = False
  - metadata.description = None
  - metadata.created_at: the time this run wrote
  - network.wsproxy_addr = None
  - network.use_host_network = False
  - scheduler.type = <SchedulerTypeDTO.FIFO: 'fifo'>
  - scheduler.preemption.enabled = False
  - scheduler.preemption.preemptible_priority = 5
  - scheduler.preemption.order = <PreemptionOrder.OLDEST: 'oldest'>
  - scheduler.preemption.mode = <PreemptionModeDTO.TERMINATE: 'terminate'>
  - scheduler.preemption.preemption_min_runtime = 0.0
  - scheduler.preemption.victim_scope = <PreemptionVictimScope.USER: 'user'>
  - default_deployment_options: skipped: the default the installation sets
  - default_session_options: skipped: the default the installation sets

<a id="fair_share-a-user-granted-nothing-may-not-change-the-fair-share-spec"></a>

#### [a-user-granted-nothing-may-not-change-the-fair-share-spec](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

a user granted nothing trying to change the half-life is rejected for not enough permission

Given

- one resource group and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 changes the half-life in the fair share config of resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="fair_share-a-weight-on-a-resource-no-agent-reports-is-rejected"></a>

#### [a-weight-on-a-resource-no-agent-reports-is-rejected](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

assigning a weight to a resource type no agent reports is rejected as an invalid input

Given

- one resource group and one regular user granted the UPDATE role in the group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 assigns a weight to no-such-slot on resource-group-1

Then

- the call is rejected
  - rejected: InvalidResourceWeightError

<a id="fair_share-changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found"></a>

#### [changing-the-fair-share-spec-of-a-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_group/test_fair_share.py): pass

when the superadmin changes the half-life of a name nothing answers to, the call is rejected because no target answers to it

Given

- one resource group and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceGroupAdapter.update_fair_share_spec: user-1 changes the half-life in the fair share config of a name that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

