## container_registry

[background](/src/ai/backend/manager/api/adapters/container_registry/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/container_registry/adapter.py)

Scenario: complete

- built from ops (5)
  - admin_partial_bulk_purge: representative success ✓ · representative rejection ✓
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - lookup_by_name_and_registry_project: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- direct implementation (6)
  - admin_create: success present 2 · rejection present 2 (global_scope, relation)
  - admin_purge: success present 2 · rejection present 2 (global_scope)
  - admin_update: success present 3 · rejection present 4 (global_scope, membership, relation)
  - apply_allowed_groups: success present 8 · rejection present 6 (relation)
  - apply_global: success present 2 · rejection present 3 (membership)
  - link_project_as_default: success present 1 · rejection present 3 (relation)

**admin_partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges two container registries and one id that does not exist at once, the two come back as they were before purging and the id that does not exist comes back in the failed list because there is no such target](#partial_bulk_purging-purging-several-registries-answers-for-the-missing-one) | answered |
| [when a user granted nothing tries to purge several container registries at once, nothing is purged and all come back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches with the global visibility filter, only container registries that are not global remain](#searching-filtering-by-global-visibility-leaves-only-non-global-registries) | answered |
| [when the superadmin searches with the type filter, only container registries of that type remain](#searching-filtering-by-type-leaves-only-matching-registries) | answered |
| [when the superadmin searches with no condition, every container registry seeded in advance comes back](#searching-searching-without-a-filter-counts-every-registry) | answered |
| [when a user who is not the superadmin tries to search container registries, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#searching-a-user-who-is-not-the-superadmin-may-not-search-registries) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [loading with an empty id list calls no lower layer and an empty answer comes back](#reading-an-empty-id-list-answers-empty-without-calling-the-wiring) | answered |
| [when the superadmin loads two container registries seeded in advance and one id that does not exist at once, the container registries seeded in advance come back in the requested order. What comes back for the entry of the id that does not exist is not decided yet](#reading-loading-many-ids-keeps-the-order) | answered |
| [when a user granted nothing loads several ids at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission. The id that does not exist also comes back with the same rejection, so whether it exists is not revealed](#reading-a-plain-user-loading-many-ids-is-refused-on-every-id) | rejected |

**lookup_by_name_and_registry_project**

| scenario | verdict |
|---|---|
| [a user with read permission can turn the name of a container registry that has no inner project name into its identifier](#looking_up-readable-registry-key-resolves) | answered |
| [a name that does not exist is rejected with the same error as when the caller lacks read permission](#looking_up-missing-registry-key-is-unresolvable) | rejected |
| [a name lookup by a user without read permission is rejected without revealing whether the target exists](#looking_up-unreadable-registry-key-is-unresolvable) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted permission to read registries in the domain to search searches scoped to that domain, with a name as the filter, an order and a page size in one request, only the registries related to that domain that match the filter come back](#scoped_searching-a-user-reading-registries-in-the-domain-scoped-searches-its-registries) | answered |
| [when a user not granted permission to read registries in the domain to search searches scoped to that domain, it is rejected for lack of permission](#scoped_searching-a-user-not-reading-registries-in-the-domain-is-refused) | rejected |

**admin_create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a container registry with an allowed project named, that relation is created too](#creating-a-project-named-while-creating-is-allowed-on-the-new-registry) | answered |
| [when the superadmin creates a container registry with only an address, a name, and a type, the node comes back with every other field empty](#creating-creating-a-registry-with-only-the-required-values-leaves-the-rest-empty) | answered |
| [when a container registry is created with a project that does not exist in the allow list, it is rejected because the project cannot be found](#creating-a-project-that-does-not-exist-is-refused-while-creating) | rejected |
| [when a user who is not the superadmin tries to create a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-registry) | rejected |

**admin_purge**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a container registry, the answer comes back holding the id it deleted](#retiring-deleting-a-registry-answers-with-the-id-it-removed) | answered |
| [when a container registry that has an allowed project is deleted, the allow list is deleted with it through the foreign key](#retiring-deleting-a-registry-takes-its-allowed-projects-with-it) | answered |
| [when a user who is not the superadmin tries to delete a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#retiring-a-user-who-is-not-the-superadmin-may-not-delete-a-registry) | rejected |
| [when an id that does not exist is deleted, it is rejected because the target cannot be found](#retiring-deleting-an-id-that-holds-no-registry-is-refused) | rejected |

**admin_update**

| scenario | verdict |
|---|---|
| [when the superadmin updates without naming a value, the node comes back with nothing changed](#editing-an-edit-that-names-no-value-changes-nothing) | answered |
| [when the superadmin changes only the address, only the address takes the new value and every other field stays as it is](#editing-changing-only-the-address-leaves-every-other-field-alone) | answered |
| [when the superadmin updates a container registry and allows a project, that relation is created](#editing-editing-a-registry-can-add-an-allowed-project) | answered |
| [when a user who is not the superadmin tries to edit a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted](#editing-a-user-who-is-not-the-superadmin-may-not-edit-a-registry) | rejected |
| [when the superadmin tries to change the address to one without a host, the step that validates the updated row rejects it as a malformed address](#editing-an-address-whose-host-is-empty-is-refused-on-update) | rejected |
| [when an id that does not exist is updated, it is rejected because the target cannot be found](#editing-editing-an-id-that-holds-no-registry-is-refused) | rejected |
| [when a container registry with an empty project is changed to the harbor type, it is rejected because harbor requires a project](#editing-turning-a-registry-into-harbor-without-a-project-is-refused) | rejected |

**apply_allowed_groups**

| scenario | verdict |
|---|---|
| [a user granted permission on both the container registry and project scopes can add that project to the allow list](#allowing_projects-a-user-granted-on-both-scopes-allows-a-project-on-a-registry) | answered |
| [adding a project that is allowed this container registry as its default to the allow list again is not rejected, and the default container registry stays as it is](#allowing_projects-allowing-a-project-already-linked-as-its-default-keeps-the-default) | answered |
| [adding a project that is already allowed to the allow list again is not rejected. The pair is skipped in the database](#allowing_projects-allowing-a-project-that-is-already-allowed-is-not-an-error) | answered |
| [an allowed project can be removed from the allow list](#allowing_projects-an-allowed-project-is-removed-from-the-allowed-list) | answered |
| [a user granted only create permission on both scopes can add a project to the allow list](#allowing_projects-create-permission-on-both-scopes-is-enough-to-allow-a-project) | answered |
| [removing a project that is allowed this container registry as its default from the allow list also removes the default container registry designation along with the association](#allowing_projects-removing-a-project-linked-as-its-default-drops-the-default) | answered |
| [a user granted only delete permission on both scopes can remove an allowed project](#allowing_projects-soft-delete-permission-on-both-scopes-is-enough-to-remove-a-project) | answered |
| [turning permission checks off lets even a user granted nothing allow a project](#allowing_projects-turning-enforcement-off-lets-an-ungranted-user-allow-a-project) | answered |
| [when a project that does not exist is added to the allow list, it is rejected because there is no such project](#allowing_projects-a-superadmin-naming-a-project-that-does-not-exist-is-refused) | rejected |
| [when none of the named projects is actually allowed, it is rejected because there is no relation to remove](#allowing_projects-a-superadmin-removing-a-project-that-was-never-allowed-is-refused) | rejected |
| [when a user granted permission on the project but not the container registry tries to allow a project, the relation operation checks permission on every named scope, so it is rejected for lack of permission](#allowing_projects-a-user-granted-on-the-project-but-not-the-registry-is-refused) | rejected |
| [when a user granted permission on the container registry but not the project tries to allow a project, the relation operation checks permission on every named scope, so it is rejected for lack of permission](#allowing_projects-a-user-granted-on-the-registry-but-not-the-project-is-refused) | rejected |
| [when a user granted only create permission on both scopes removes a project, it is rejected for lack of permission](#allowing_projects-create-permission-does-not-allow-removing-a-project) | rejected |
| [when a user granted only delete permission on both scopes adds a project, it is rejected for lack of permission](#allowing_projects-soft-delete-permission-does-not-allow-adding-a-project) | rejected |

**apply_global**

| scenario | verdict |
|---|---|
| [when a user granted update permission on the registry and on public sets the registry not global, the same registry comes back whole with global false](#setting_global-a-user-granted-on-both-scopes-takes-a-registry-out-of-public) | answered |
| [when the superadmin sets a registry not global, the same registry comes back whole with global false](#setting_global-the-superadmin-takes-a-registry-out-of-public) | answered |
| [when a user granted nothing tries to change a registry's visibility, it is rejected for lack of permission. This call checks permission on the registry and on the public scope together](#setting_global-a-user-granted-nothing-may-not-change-a-registry-visibility) | rejected |
| [when a user granted update permission on public but not on the registry tries to change a registry's visibility, it is rejected for lack of permission. This call does not pass with only one of the two scopes permitting it](#setting_global-a-user-granted-on-public-but-not-the-registry-may-not-change-a-registry-visibility) | rejected |
| [when a user granted update permission on the registry but not on public tries to change a registry's visibility, it is rejected for lack of permission. This call does not pass with only one of the two scopes permitting it](#setting_global-a-user-granted-on-the-registry-but-not-public-may-not-change-a-registry-visibility) | rejected |

**link_project_as_default**

| scenario | verdict |
|---|---|
| [a user granted create permission on both the container registry and the project can create an association between the project and the container registry and make it the default](#linking_default_project-create-permission-on-both-scopes-links-a-project-as-its-default) | answered |
| [when a project that already has an association with the container registry is made to create an association and designate it as the default, it is rejected because the existing association stays and it cannot be made the default](#linking_default_project-a-project-already-allowed-on-the-registry-cannot-link-it-as-a-default) | rejected |
| [when a project that already has another container registry as its default is made to create an association and designate it as the default, it is rejected because a project has only one default container registry, and the existing default container registry stays](#linking_default_project-a-project-that-already-has-a-default-registry-cannot-link-another) | rejected |
| [when a user granted permission on the container registry but not the project tries to create an association and make it the default, the relation operation checks permission on every named scope, so it is rejected for lack of permission](#linking_default_project-a-user-granted-on-the-registry-but-not-the-project-cannot-link-a-default) | rejected |

### admin_partial_bulk_purge

<a id="partial_bulk_purging-purging-several-registries-answers-for-the-missing-one"></a>

#### [purging-several-registries-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/container_registry/test_partial_bulk_purging.py): pass

when the superadmin purges two container registries and one id that does not exist at once, the two come back as they were before purging and the id that does not exist comes back in the failed list because there is no such target

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_partial_bulk_purge: user-1 purges 2 container registries and one id that does not exist at once

Then

- every container registry seeded in advance comes back as it was before it was purged, and the id that does not exist comes back in the failed list because there is no such target
  - successes count = 2
  - successes[0].id: same as the id of the container registry seeded in advance
  - successes[0].entity_id: same as the id of the container registry seeded in advance
  - successes[0].url = 'https://wanted-1.scenario.local'
  - successes[0].registry_name = 'wanted-1'
  - successes[0].type = <ContainerRegistryType.DOCKER: 'docker'>
  - successes[0].project = None
  - successes[0].username = None
  - successes[0].ssl_verify = True
  - successes[0].is_global = True
  - successes[0].extra = None
  - successes[1].id: same as the id of the container registry seeded in advance
  - successes[1].entity_id: same as the id of the container registry seeded in advance
  - successes[1].url = 'https://other-1.scenario.local'
  - successes[1].registry_name = 'other-1'
  - successes[1].type = <ContainerRegistryType.HARBOR2: 'harbor2'>
  - successes[1].project = None
  - successes[1].username = None
  - successes[1].ssl_verify = True
  - successes[1].is_global = False
  - successes[1].extra = None
  - failed count = 1
  - failed[0].id: same as the id that does not exist put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-registries"></a>

#### [a-user-granted-nothing-purges-none-of-several-registries](/tests/scenario/bai_scenario/manager/container_registry/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several container registries at once, nothing is purged and all come back in the failed list because there is no permission

Given

- two registries and one user
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_partial_bulk_purge: user-1 purges 2 container registries at once

Then

- no container registry is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the container registry seeded in advance
  - rejected: failed[0]: Insufficient permission
  - failed[1].id: same as the id of the container registry seeded in advance
  - rejected: failed[1]: Insufficient permission

### admin_search

<a id="searching-filtering-by-global-visibility-leaves-only-non-global-registries"></a>

#### [filtering-by-global-visibility-leaves-only-non-global-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py): pass

when the superadmin searches with the global visibility filter, only container registries that are not global remain

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_search: user-1 searches with the non-global filter

Then

- only container registries that are not global come back
  - items: same as the container registries seeded in advance
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-by-type-leaves-only-matching-registries"></a>

#### [filtering-by-type-leaves-only-matching-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py): pass

when the superadmin searches with the type filter, only container registries of that type remain

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_search: user-1 searches with the type filter

Then

- only one container registry that matches the filter remains
  - items: same as the container registries seeded in advance
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-searching-without-a-filter-counts-every-registry"></a>

#### [searching-without-a-filter-counts-every-registry](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py): pass

when the superadmin searches with no condition, every container registry seeded in advance comes back

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_search: user-1 searches with no condition

Then

- every container registry seeded in advance is counted
  - items: same as the container registries seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-registries"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-registries](/tests/scenario/bai_scenario/manager/container_registry/test_searching.py): pass

when a user who is not the superadmin tries to search container registries, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- two registries and one user
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_search: user-1 searches with no condition

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-an-empty-id-list-answers-empty-without-calling-the-wiring"></a>

#### [an-empty-id-list-answers-empty-without-calling-the-wiring](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py): pass

loading with an empty id list calls no lower layer and an empty answer comes back

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.batch_load_by_ids: user-1 loads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading-loading-many-ids-keeps-the-order"></a>

#### [loading-many-ids-keeps-the-order](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py): pass

when the superadmin loads two container registries seeded in advance and one id that does not exist at once, the container registries seeded in advance come back in the requested order. What comes back for the entry of the id that does not exist is not decided yet

Given

- two registries and one superadmin
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.batch_load_by_ids: user-1 loads two container registries seeded in advance and one id that does not exist at once

Then

- the container registries seeded in advance come back in the requested order, and the entry for the id that does not exist is not checked
  - length = 3
  - [0].registry_name = 'wanted-1'
  - [1]: skipped: the response a superadmin gets for an id that does not exist is not decided yet
  - [2].registry_name = 'other-1'

<a id="reading-a-plain-user-loading-many-ids-is-refused-on-every-id"></a>

#### [a-plain-user-loading-many-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/container_registry/test_reading.py): pass

when a user granted nothing loads several ids at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission. The id that does not exist also comes back with the same rejection, so whether it exists is not revealed

Given

- two registries and one user
  - Domain home-1
  - Container registry wanted-1: image source
  - Container registry other-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.batch_load_by_ids: user-1 loads two container registries seeded in advance and one id that does not exist at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### lookup_by_name_and_registry_project

<a id="looking_up-readable-registry-key-resolves"></a>

#### [readable-registry-key-resolves](/tests/scenario/bai_scenario/manager/container_registry/test_looking_up.py): pass

a user with read permission can turn the name of a container registry that has no inner project name into its identifier

Given

- one registry, one project, and one user holding permission on the registry
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: READ allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1

When

- ContainerRegistryAdapter.lookup_by_name_and_registry_project: a plain user looks up the container registry identifier by name and the project name inside the container registry

Then

- the identifier of the container registry prepared comes back
  - registry: same as the container registry prepared

<a id="looking_up-missing-registry-key-is-unresolvable"></a>

#### [missing-registry-key-is-unresolvable](/tests/scenario/bai_scenario/manager/container_registry/test_looking_up.py): pass

a name that does not exist is rejected with the same error as when the caller lacks read permission

Given

- one registry, one project, and one user holding permission on the registry
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: READ allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1

When

- ContainerRegistryAdapter.lookup_by_name_and_registry_project: a plain user looks up the container registry identifier by name and the project name inside the container registry

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="looking_up-unreadable-registry-key-is-unresolvable"></a>

#### [unreadable-registry-key-is-unresolvable](/tests/scenario/bai_scenario/manager/container_registry/test_looking_up.py): pass

a name lookup by a user without read permission is rejected without revealing whether the target exists

Given

- one registry, one project, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.lookup_by_name_and_registry_project: a plain user looks up the container registry identifier by name and the project name inside the container registry

Then

- the call is rejected
  - rejected: GenericBadRequest

### scoped_search

<a id="scoped_searching-a-user-reading-registries-in-the-domain-scoped-searches-its-registries"></a>

#### [a-user-reading-registries-in-the-domain-scoped-searches-its-registries](/tests/scenario/bai_scenario/manager/container_registry/test_scoped_searching.py): pass

when a user granted permission to read registries in the domain to search searches scoped to that domain, with a name as the filter, an order and a page size in one request, only the registries related to that domain that match the filter come back

Given

- four relations between two domains and three registries, and one user in one of the domains granted permission to read registries in that domain. One registry is not related to that domain
  - Domain home-1
  - Domain other-1
  - Container registry wanted-1: image source
  - Container registry other-2: image source
  - Container registry outside-1: image source
  - Domain home-1 allows Container registry wanted-1
  - Domain home-1 allows Container registry other-2
  - Domain other-1 allows Container registry wanted-1
  - Domain other-1 allows Container registry outside-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the read-registries-in-domain permission
    - Role read-registries-in-domain-1: applies only within the scope it is granted in
    - Role read-registries-in-domain-1: READ allowed on every container_registry
    - regular user user-1: holds Role read-registries-in-domain-1

When

- ContainerRegistryAdapter.scoped_search: user-1 reads scoped to the domain to search, with the name of the wanted registry as the filter, the name order and a page size in one request

Then

- only the wanted registry among those related to the domain to search comes back whole, and neither the registry the filter excludes nor the registry not related to the domain to search does
  - total_count = 1
  - items count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the wanted registry
  - items[0].entity_id: same as the id of the wanted registry
  - items[0].url: same as the url of the wanted registry
  - items[0].registry_name: same as the name of the wanted registry
  - items[0].type = <ContainerRegistryType.DOCKER: 'docker'>
  - items[0].project = None
  - items[0].username = None
  - items[0].ssl_verify = True
  - items[0].is_global = True
  - items[0].extra = None

<a id="scoped_searching-a-user-not-reading-registries-in-the-domain-is-refused"></a>

#### [a-user-not-reading-registries-in-the-domain-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_scoped_searching.py): pass

when a user not granted permission to read registries in the domain to search searches scoped to that domain, it is rejected for lack of permission

Given

- four relations between two domains and three registries, and one user in one of the domains granted nothing. One registry is not related to that domain
  - Domain home-1
  - Domain other-1
  - Container registry wanted-1: image source
  - Container registry other-2: image source
  - Container registry outside-1: image source
  - Domain home-1 allows Container registry wanted-1
  - Domain home-1 allows Container registry other-2
  - Domain other-1 allows Container registry wanted-1
  - Domain other-1 allows Container registry outside-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.scoped_search: user-1 reads scoped to the domain to search, with the name of the wanted registry as the filter, the name order and a page size in one request

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_create

<a id="creating-a-project-named-while-creating-is-allowed-on-the-new-registry"></a>

#### [a-project-named-while-creating-is-allowed-on-the-new-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py): pass

when the superadmin creates a container registry with an allowed project named, that relation is created too

Given

- no registry, one project, and one superadmin in one domain
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_create: user-1 creates a container registry at https://made.scenario.local adding the project made in advance to the allow list

Then

- the whole created registry comes back
  - entity_id: same as the id in the response
  - url = 'https://made.scenario.local'
  - registry_name = 'made-registry'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: skipped: the database generates it

<a id="creating-creating-a-registry-with-only-the-required-values-leaves-the-rest-empty"></a>

#### [creating-a-registry-with-only-the-required-values-leaves-the-rest-empty](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py): pass

when the superadmin creates a container registry with only an address, a name, and a type, the node comes back with every other field empty

Given

- no registry, one project, and one superadmin in one domain
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_create: user-1 creates a container registry at https://made.scenario.local with no allow list

Then

- the whole created registry comes back
  - entity_id: same as the id in the response
  - url = 'https://made.scenario.local'
  - registry_name = 'made-registry'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: skipped: the database generates it

<a id="creating-a-project-that-does-not-exist-is-refused-while-creating"></a>

#### [a-project-that-does-not-exist-is-refused-while-creating](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py): pass

when a container registry is created with a project that does not exist in the allow list, it is rejected because the project cannot be found

Given

- no registry, one project, and one superadmin in one domain
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_create: user-1 creates a container registry at https://made.scenario.local adding a project that does not exist to the allow list

Then

- the call is rejected
  - rejected: ProjectNotFound

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_creating.py): pass

when a user who is not the superadmin tries to create a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- no registry, one project, and one user in one domain
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_create: user-1 creates a container registry at https://made.scenario.local with no allow list

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_purge

<a id="retiring-deleting-a-registry-answers-with-the-id-it-removed"></a>

#### [deleting-a-registry-answers-with-the-id-it-removed](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py): pass

when the superadmin deletes a container registry, the answer comes back holding the id it deleted

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_purge: user-1 deletes the registry made in advance

Then

- the id that was deleted comes back
  - id: same as the id of the container registry seeded in advance
  - entity_id: same as the id of the container registry seeded in advance

<a id="retiring-deleting-a-registry-takes-its-allowed-projects-with-it"></a>

#### [deleting-a-registry-takes-its-allowed-projects-with-it](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py): pass

when a container registry that has an allowed project is deleted, the allow list is deleted with it through the foreign key

Given

- one registry, one project already allowed to it, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_purge: user-1 deletes the registry made in advance

Then

- the id that was deleted comes back
  - id: same as the id of the container registry seeded in advance
  - entity_id: same as the id of the container registry seeded in advance

<a id="retiring-a-user-who-is-not-the-superadmin-may-not-delete-a-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-delete-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py): pass

when a user who is not the superadmin tries to delete a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- one registry, and one user
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_purge: user-1 deletes the registry made in advance

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="retiring-deleting-an-id-that-holds-no-registry-is-refused"></a>

#### [deleting-an-id-that-holds-no-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_retiring.py): pass

when an id that does not exist is deleted, it is rejected because the target cannot be found

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_purge: user-1 deletes an id that does not exist

Then

- the call is rejected
  - rejected: ContainerRegistryNotFound

### admin_update

<a id="editing-an-edit-that-names-no-value-changes-nothing"></a>

#### [an-edit-that-names-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when the superadmin updates without naming a value, the node comes back with nothing changed

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 updates without naming any value

Then

- the whole registry made in advance comes back
  - entity_id: same as the id of the registry seeded in advance
  - url = 'https://host-1.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: skipped: the database generates it

<a id="editing-changing-only-the-address-leaves-every-other-field-alone"></a>

#### [changing-only-the-address-leaves-every-other-field-alone](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when the superadmin changes only the address, only the address takes the new value and every other field stays as it is

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 changes the address to https://moved.scenario.local

Then

- the whole registry made in advance comes back
  - entity_id: same as the id of the registry seeded in advance
  - url = 'https://moved.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: skipped: the database generates it

<a id="editing-editing-a-registry-can-add-an-allowed-project"></a>

#### [editing-a-registry-can-add-an-allowed-project](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when the superadmin updates a container registry and allows a project, that relation is created

Given

- one registry, one project, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 updates it while adding the project seeded in advance to the allow list

Then

- the whole registry made in advance comes back
  - entity_id: same as the id of the registry seeded in advance
  - url = 'https://host-1.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - ssl_verify = True
  - is_global = True
  - extra = None
  - id: skipped: the database generates it

<a id="editing-a-user-who-is-not-the-superadmin-may-not-edit-a-registry"></a>

#### [a-user-who-is-not-the-superadmin-may-not-edit-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when a user who is not the superadmin tries to edit a container registry, it is rejected for lack of permission. This call checks only whether the caller is the superadmin and does not look at the permissions granted

Given

- one registry, and one user
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 changes the address to https://moved.scenario.local

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="editing-an-address-whose-host-is-empty-is-refused-on-update"></a>

#### [an-address-whose-host-is-empty-is-refused-on-update](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when the superadmin tries to change the address to one without a host, the step that validates the updated row rejects it as a malformed address

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 changes the address to http://

Then

- the call is rejected
  - rejected: InvalidContainerRegistryURL

<a id="editing-editing-an-id-that-holds-no-registry-is-refused"></a>

#### [editing-an-id-that-holds-no-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when an id that does not exist is updated, it is rejected because the target cannot be found

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 updates an id that does not exist

Then

- the call is rejected
  - rejected: ContainerRegistryNotFound

<a id="editing-turning-a-registry-into-harbor-without-a-project-is-refused"></a>

#### [turning-a-registry-into-harbor-without-a-project-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_editing.py): pass

when a container registry with an empty project is changed to the harbor type, it is rejected because harbor requires a project

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.admin_update: user-1 changes the type to harbor2

Then

- the call is rejected
  - rejected: InvalidContainerRegistryProject

### apply_allowed_groups

<a id="allowing_projects-a-user-granted-on-both-scopes-allows-a-project-on-a-registry"></a>

#### [a-user-granted-on-both-scopes-allows-a-project-on-a-registry](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

a user granted permission on both the container registry and project scopes can add that project to the allow list

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-allowing-a-project-already-linked-as-its-default-keeps-the-default"></a>

#### [allowing-a-project-already-linked-as-its-default-keeps-the-default](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

adding a project that is allowed this container registry as its default to the allow list again is not rejected, and the default container registry stays as it is

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project already has this registry as its default
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 defaults to Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-allowing-a-project-that-is-already-allowed-is-not-an-error"></a>

#### [allowing-a-project-that-is-already-allowed-is-not-an-error](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

adding a project that is already allowed to the allow list again is not rejected. The pair is skipped in the database

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project is already allowed
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-an-allowed-project-is-removed-from-the-allowed-list"></a>

#### [an-allowed-project-is-removed-from-the-allowed-list](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

an allowed project can be removed from the allow list

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project is already allowed
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 removed from the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-create-permission-on-both-scopes-is-enough-to-allow-a-project"></a>

#### [create-permission-on-both-scopes-is-enough-to-allow-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

a user granted only create permission on both scopes can add a project to the allow list

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-removing-a-project-linked-as-its-default-drops-the-default"></a>

#### [removing-a-project-linked-as-its-default-drops-the-default](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

removing a project that is allowed this container registry as its default from the allow list also removes the default container registry designation along with the association

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project already has this registry as its default
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 defaults to Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 removed from the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-soft-delete-permission-on-both-scopes-is-enough-to-remove-a-project"></a>

#### [soft-delete-permission-on-both-scopes-is-enough-to-remove-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

a user granted only delete permission on both scopes can remove an allowed project

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project is already allowed
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 removed from the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-turning-enforcement-off-lets-an-ungranted-user-allow-a-project"></a>

#### [turning-enforcement-off-lets-an-ungranted-user-allow-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

turning permission checks off lets even a user granted nothing allow a project

Given

- one registry, one project, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- nothing is returned and no exception is raised
  - response = None

<a id="allowing_projects-a-superadmin-naming-a-project-that-does-not-exist-is-refused"></a>

#### [a-superadmin-naming-a-project-that-does-not-exist-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when a project that does not exist is added to the allow list, it is rejected because there is no such project

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - superadmin user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - superadmin user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 a project that does not exist added to the allow list

Then

- the call is rejected
  - rejected: ProjectNotFound

<a id="allowing_projects-a-superadmin-removing-a-project-that-was-never-allowed-is-refused"></a>

#### [a-superadmin-removing-a-project-that-was-never-allowed-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when none of the named projects is actually allowed, it is rejected because there is no relation to remove

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - superadmin user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - superadmin user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 removed from the allow list

Then

- the call is rejected
  - rejected: ContainerRegistryGroupsAssociationNotFound

<a id="allowing_projects-a-user-granted-on-the-project-but-not-the-registry-is-refused"></a>

#### [a-user-granted-on-the-project-but-not-the-registry-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when a user granted permission on the project but not the container registry tries to allow a project, the relation operation checks permission on every named scope, so it is rejected for lack of permission

Given

- one registry, one project, and one user holding permission on the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="allowing_projects-a-user-granted-on-the-registry-but-not-the-project-is-refused"></a>

#### [a-user-granted-on-the-registry-but-not-the-project-is-refused](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when a user granted permission on the container registry but not the project tries to allow a project, the relation operation checks permission on every named scope, so it is rejected for lack of permission

Given

- one registry, one project, and one user holding permission on the registry
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="allowing_projects-create-permission-does-not-allow-removing-a-project"></a>

#### [create-permission-does-not-allow-removing-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when a user granted only create permission on both scopes removes a project, it is rejected for lack of permission

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project is already allowed
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 removed from the allow list

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="allowing_projects-soft-delete-permission-does-not-allow-adding-a-project"></a>

#### [soft-delete-permission-does-not-allow-adding-a-project](/tests/scenario/bai_scenario/manager/container_registry/test_allowing_projects.py): pass

when a user granted only delete permission on both scopes adds a project, it is rejected for lack of permission

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: SOFT_DELETE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: SOFT_DELETE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.apply_allowed_groups: user-1 added to the allow list

Then

- the call is rejected
  - rejected: NotEnoughPermission

### apply_global

<a id="setting_global-a-user-granted-on-both-scopes-takes-a-registry-out-of-public"></a>

#### [a-user-granted-on-both-scopes-takes-a-registry-out-of-public](/tests/scenario/bai_scenario/manager/container_registry/test_setting_global.py): pass

when a user granted update permission on the registry and on public sets the registry not global, the same registry comes back whole with global false

Given

- one registry, and one user, granted update on the registry and on public
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted update permission on the registry, public
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: UPDATE allowed on every container_registry
    - regular user user-1: holds Role registry-keeper-1
    - Role public-registry-keeper-1: applies only within the scope it is granted in
    - Role public-registry-keeper-1: UPDATE allowed on every global
    - regular user user-1: holds Role public-registry-keeper-1

When

- ContainerRegistryAdapter.apply_global: user-1 changes whether host-1 is global

Then

- the whole seeded registry comes back with the new visibility
  - id: same as the id of the container registry seeded in advance
  - url = 'https://host-1.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - password = None
  - ssl_verify = True
  - is_global = False
  - extra = None

<a id="setting_global-the-superadmin-takes-a-registry-out-of-public"></a>

#### [the-superadmin-takes-a-registry-out-of-public](/tests/scenario/bai_scenario/manager/container_registry/test_setting_global.py): pass

when the superadmin sets a registry not global, the same registry comes back whole with global false

Given

- one registry, and one superadmin
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.apply_global: user-1 changes whether host-1 is global

Then

- the whole seeded registry comes back with the new visibility
  - id: same as the id of the container registry seeded in advance
  - url = 'https://host-1.scenario.local'
  - registry_name = 'host-1'
  - type = <ContainerRegistryType.DOCKER: 'docker'>
  - project = None
  - username = None
  - password = None
  - ssl_verify = True
  - is_global = False
  - extra = None

<a id="setting_global-a-user-granted-nothing-may-not-change-a-registry-visibility"></a>

#### [a-user-granted-nothing-may-not-change-a-registry-visibility](/tests/scenario/bai_scenario/manager/container_registry/test_setting_global.py): pass

when a user granted nothing tries to change a registry's visibility, it is rejected for lack of permission. This call checks permission on the registry and on the public scope together

Given

- one registry, and one user
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ContainerRegistryAdapter.apply_global: user-1 changes whether host-1 is global

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="setting_global-a-user-granted-on-public-but-not-the-registry-may-not-change-a-registry-visibility"></a>

#### [a-user-granted-on-public-but-not-the-registry-may-not-change-a-registry-visibility](/tests/scenario/bai_scenario/manager/container_registry/test_setting_global.py): pass

when a user granted update permission on public but not on the registry tries to change a registry's visibility, it is rejected for lack of permission. This call does not pass with only one of the two scopes permitting it

Given

- one registry, and one user, granted update on public and not on the registry
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted update permission on public
    - Role public-registry-keeper-1: applies only within the scope it is granted in
    - Role public-registry-keeper-1: UPDATE allowed on every global
    - regular user user-1: holds Role public-registry-keeper-1

When

- ContainerRegistryAdapter.apply_global: user-1 changes whether host-1 is global

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="setting_global-a-user-granted-on-the-registry-but-not-public-may-not-change-a-registry-visibility"></a>

#### [a-user-granted-on-the-registry-but-not-public-may-not-change-a-registry-visibility](/tests/scenario/bai_scenario/manager/container_registry/test_setting_global.py): pass

when a user granted update permission on the registry but not on public tries to change a registry's visibility, it is rejected for lack of permission. This call does not pass with only one of the two scopes permitting it

Given

- one registry, and one user, granted update on the registry and not on public
  - Domain home-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted update permission on the registry
    - Role registry-keeper-1: applies only within the scope it is granted in
    - Role registry-keeper-1: UPDATE allowed on every container_registry
    - regular user user-1: holds Role registry-keeper-1

When

- ContainerRegistryAdapter.apply_global: user-1 changes whether host-1 is global

Then

- the call is rejected
  - rejected: NotEnoughPermission

### link_project_as_default

<a id="linking_default_project-create-permission-on-both-scopes-links-a-project-as-its-default"></a>

#### [create-permission-on-both-scopes-links-a-project-as-its-default](/tests/scenario/bai_scenario/manager/container_registry/test_linking_default_project.py): pass

a user granted create permission on both the container registry and the project can create an association between the project and the container registry and make it the default

Given

- one registry, one project, and one user holding permission on the registry and the project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.link_project_as_default: user-1 creates an association between the project and the container registry and makes it the default

Then

- nothing is returned and no exception is raised
  - response = None

<a id="linking_default_project-a-project-already-allowed-on-the-registry-cannot-link-it-as-a-default"></a>

#### [a-project-already-allowed-on-the-registry-cannot-link-it-as-a-default](/tests/scenario/bai_scenario/manager/container_registry/test_linking_default_project.py): pass

when a project that already has an association with the container registry is made to create an association and designate it as the default, it is rejected because the existing association stays and it cannot be made the default

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project is already allowed
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Project project-1 allows Container registry host-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.link_project_as_default: user-1 creates an association between the project and the container registry and makes it the default

Then

- the call is rejected
  - rejected: ProjectDefaultContainerRegistryConflict

<a id="linking_default_project-a-project-that-already-has-a-default-registry-cannot-link-another"></a>

#### [a-project-that-already-has-a-default-registry-cannot-link-another](/tests/scenario/bai_scenario/manager/container_registry/test_linking_default_project.py): pass

when a project that already has another container registry as its default is made to create an association and designate it as the default, it is rejected because a project has only one default container registry, and the existing default container registry stays

Given

- one registry, one project, and one user holding permission on the registry and the project, and the project has another default registry
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Container registry other-1: image source
  - Project project-1 defaults to Container registry other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1
  - Prepare a user granted the allow-on-project permission
    - Role allow-on-project-1: applies only within the scope it is granted in
    - Role allow-on-project-1: CREATE allowed on every project
    - regular user user-1: holds Role allow-on-project-1

When

- ContainerRegistryAdapter.link_project_as_default: user-1 creates an association between the project and the container registry and makes it the default

Then

- the call is rejected
  - rejected: ProjectDefaultContainerRegistryConflict

<a id="linking_default_project-a-user-granted-on-the-registry-but-not-the-project-cannot-link-a-default"></a>

#### [a-user-granted-on-the-registry-but-not-the-project-cannot-link-a-default](/tests/scenario/bai_scenario/manager/container_registry/test_linking_default_project.py): pass

when a user granted permission on the container registry but not the project tries to create an association and make it the default, the relation operation checks permission on every named scope, so it is rejected for lack of permission

Given

- one registry, one project, and one user holding permission on the registry
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project project-1
  - Container registry host-1: image source
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the allow-on-registry permission
    - Role allow-on-registry-1: applies only within the scope it is granted in
    - Role allow-on-registry-1: CREATE allowed on every container_registry
    - regular user user-1: holds Role allow-on-registry-1

When

- ContainerRegistryAdapter.link_project_as_default: user-1 creates an association between the project and the container registry and makes it the default

Then

- the call is rejected
  - rejected: NotEnoughPermission

