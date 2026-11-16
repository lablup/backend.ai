## resource_usage

[adapter](/src/ai/backend/manager/api/adapters/resource_usage/adapter.py)

Scenario: complete

- built from ops (14)
  - admin_search_domain: representative success ✓ · representative rejection ✓
  - admin_search_project: representative success ✓ · representative rejection ✓
  - admin_search_user: representative success ✓ · representative rejection ✓
  - domain_search_domain: representative success ✓ · representative rejection ✓
  - domain_search_project: representative success ✓ · representative rejection ✓
  - domain_search_user: representative success ✓ · representative rejection ✓
  - gql_admin_search_domain: representative success ✓ · representative rejection ✓
  - gql_admin_search_project: representative success ✓ · representative rejection ✓
  - gql_admin_search_user: representative success ✓ · representative rejection ✓
  - gql_search_domain_scoped: representative success ✓ · representative rejection ✓
  - gql_search_project_scoped: representative success ✓ · representative rejection ✓
  - gql_search_project_unscoped: representative success ✓ · representative rejection ✓
  - gql_search_user_scoped: representative success ✓ · representative rejection ✓
  - gql_search_user_unscoped: representative success ✓ · representative rejection ✓

**admin_search_domain**

| scenario | verdict |
|---|---|
| [when the superadmin pages through domain usage buckets where none are laid, an empty page comes back](#searching-admin-search-domain-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through domain usage buckets, the call is rejected](#searching-admin-search-domain-is-refused-to-a-caller-without-permission) | rejected |

**admin_search_project**

| scenario | verdict |
|---|---|
| [when the superadmin pages through project usage buckets where none are laid, an empty page comes back](#searching-admin-search-project-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through project usage buckets, the call is rejected](#searching-admin-search-project-is-refused-to-a-caller-without-permission) | rejected |

**admin_search_user**

| scenario | verdict |
|---|---|
| [when the superadmin pages through user usage buckets where none are laid, an empty page comes back](#searching-admin-search-user-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through user usage buckets, the call is rejected](#searching-admin-search-user-is-refused-to-a-caller-without-permission) | rejected |

**domain_search_domain**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through domain usage buckets where none are laid, an empty page comes back](#searching-domain-search-domain-returns-an-empty-page) | answered |
| [when a user granted nothing pages through domain usage buckets, the call is rejected](#searching-domain-search-domain-is-refused-to-a-caller-without-permission) | rejected |

**domain_search_project**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through project usage buckets where none are laid, an empty page comes back](#searching-domain-search-project-returns-an-empty-page) | answered |
| [when a user granted nothing pages through project usage buckets, the call is rejected](#searching-domain-search-project-is-refused-to-a-caller-without-permission) | rejected |

**domain_search_user**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through user usage buckets where none are laid, an empty page comes back](#searching-domain-search-user-returns-an-empty-page) | answered |
| [when a user granted nothing pages through user usage buckets, the call is rejected](#searching-domain-search-user-is-refused-to-a-caller-without-permission) | rejected |

**gql_admin_search_domain**

| scenario | verdict |
|---|---|
| [when the superadmin pages through domain usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-admin-search-domain-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through domain usage buckets through the GQL path, the call is rejected](#gql_searching-gql-admin-search-domain-is-refused-to-a-caller-without-permission) | rejected |

**gql_admin_search_project**

| scenario | verdict |
|---|---|
| [when the superadmin pages through project usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-admin-search-project-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through project usage buckets through the GQL path, the call is rejected](#gql_searching-gql-admin-search-project-is-refused-to-a-caller-without-permission) | rejected |

**gql_admin_search_user**

| scenario | verdict |
|---|---|
| [when the superadmin pages through user usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-admin-search-user-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through user usage buckets through the GQL path, the call is rejected](#gql_searching-gql-admin-search-user-is-refused-to-a-caller-without-permission) | rejected |

**gql_search_domain_scoped**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through domain usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-search-domain-scoped-returns-an-empty-page) | answered |
| [when a user granted nothing pages through domain usage buckets through the GQL path, the call is rejected](#gql_searching-gql-search-domain-scoped-is-refused-to-a-caller-without-permission) | rejected |

**gql_search_project_scoped**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through project usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-search-project-scoped-returns-an-empty-page) | answered |
| [when a user granted nothing pages through project usage buckets through the GQL path, the call is rejected](#gql_searching-gql-search-project-scoped-is-refused-to-a-caller-without-permission) | rejected |

**gql_search_project_unscoped**

| scenario | verdict |
|---|---|
| [when the superadmin pages through project usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-search-project-unscoped-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through project usage buckets through the GQL path, the call is rejected](#gql_searching-gql-search-project-unscoped-is-refused-to-a-caller-without-permission) | rejected |

**gql_search_user_scoped**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read usage in the resource group pages through user usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-search-user-scoped-returns-an-empty-page) | answered |
| [when a user granted nothing pages through user usage buckets through the GQL path, the call is rejected](#gql_searching-gql-search-user-scoped-is-refused-to-a-caller-without-permission) | rejected |

**gql_search_user_unscoped**

| scenario | verdict |
|---|---|
| [when the superadmin pages through user usage buckets through the GQL path where none are laid, an empty page comes back](#gql_searching-gql-search-user-unscoped-returns-an-empty-page) | answered |
| [when a user other than the superadmin pages through user usage buckets through the GQL path, the call is rejected](#gql_searching-gql-search-user-unscoped-is-refused-to-a-caller-without-permission) | rejected |

### admin_search_domain

<a id="searching-admin-search-domain-returns-an-empty-page"></a>

#### [admin-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when the superadmin pages through domain usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 without a scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user other than the superadmin pages through domain usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 without a scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_project

<a id="searching-admin-search-project-returns-an-empty-page"></a>

#### [admin-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when the superadmin pages through project usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 without a scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-project-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user other than the superadmin pages through project usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 without a scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_user

<a id="searching-admin-search-user-returns-an-empty-page"></a>

#### [admin-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when the superadmin pages through user usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 without a scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-admin-search-user-is-refused-to-a-caller-without-permission"></a>

#### [admin-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user other than the superadmin pages through user usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.admin_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 without a scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### domain_search_domain

<a id="searching-domain-search-domain-returns-an-empty-page"></a>

#### [domain-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through domain usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.domain_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 as the scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user granted nothing pages through domain usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.domain_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 as the scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### domain_search_project

<a id="searching-domain-search-project-returns-an-empty-page"></a>

#### [domain-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through project usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.domain_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 as the scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-project-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user granted nothing pages through project usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.domain_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 as the scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### domain_search_user

<a id="searching-domain-search-user-returns-an-empty-page"></a>

#### [domain-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through user usage buckets where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.domain_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 as the scope

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-domain-search-user-is-refused-to-a-caller-without-permission"></a>

#### [domain-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_searching.py): pass

when a user granted nothing pages through user usage buckets, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.domain_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 as the scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### gql_admin_search_domain

<a id="gql_searching-gql-admin-search-domain-returns-an-empty-page"></a>

#### [gql-admin-search-domain-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when the superadmin pages through domain usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-domain-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-domain-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user other than the superadmin pages through domain usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_domain: user-2 pages through the domain usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### gql_admin_search_project

<a id="gql_searching-gql-admin-search-project-returns-an-empty-page"></a>

#### [gql-admin-search-project-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when the superadmin pages through project usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-project-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-project-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user other than the superadmin pages through project usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_project: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### gql_admin_search_user

<a id="gql_searching-gql-admin-search-user-returns-an-empty-page"></a>

#### [gql-admin-search-user-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when the superadmin pages through user usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-admin-search-user-is-refused-to-a-caller-without-permission"></a>

#### [gql-admin-search-user-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user other than the superadmin pages through user usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_admin_search_user: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### gql_search_domain_scoped

<a id="gql_searching-gql-search-domain-scoped-returns-an-empty-page"></a>

#### [gql-search-domain-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through domain usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.gql_search_domain_scoped: user-2 pages through the domain usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-domain-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-domain-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user granted nothing pages through domain usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_domain_scoped: user-2 pages through the domain usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: NotEnoughPermission

### gql_search_project_scoped

<a id="gql_searching-gql-search-project-scoped-returns-an-empty-page"></a>

#### [gql-search-project-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through project usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.gql_search_project_scoped: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-project-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-project-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user granted nothing pages through project usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_project_scoped: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: NotEnoughPermission

### gql_search_project_unscoped

<a id="gql_searching-gql-search-project-unscoped-returns-an-empty-page"></a>

#### [gql-search-project-unscoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when the superadmin pages through project usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_project_unscoped: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-project-unscoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-project-unscoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user other than the superadmin pages through project usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_project_unscoped: user-2 pages through the project usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### gql_search_user_scoped

<a id="gql_searching-gql-search-user-scoped-returns-an-empty-page"></a>

#### [gql-search-user-scoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a regular user granted permission to read usage in the resource group pages through user usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user granted permission to read domain, project and user usage in the resource group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Role usage-reader-1: applies only within the scope it is granted in
  - Role usage-reader-1: READ allowed on every domain
  - Role usage-reader-1: READ allowed on every project
  - Role usage-reader-1: READ allowed on every user
  - regular user user-2: holds Role usage-reader-1

When

- ResourceUsageAdapter.gql_search_user_scoped: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-user-scoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-user-scoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user granted nothing pages through user usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_user_scoped: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: NotEnoughPermission

### gql_search_user_unscoped

<a id="gql_searching-gql-search-user-unscoped-returns-an-empty-page"></a>

#### [gql-search-user-unscoped-returns-an-empty-page](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when the superadmin pages through user usage buckets through the GQL path where none are laid, an empty page comes back

Given

- a domain, resource group, project and user to page usage buckets for, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_user_unscoped: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="gql_searching-gql-search-user-unscoped-is-refused-to-a-caller-without-permission"></a>

#### [gql-search-user-unscoped-is-refused-to-a-caller-without-permission](/tests/scenario/bai_scenario/manager/resource_usage/test_gql_searching.py): pass

when a user other than the superadmin pages through user usage buckets through the GQL path, the call is rejected

Given

- a domain, resource group, project and user to page usage buckets for, and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image

When

- ResourceUsageAdapter.gql_search_user_unscoped: user-2 pages through the user usage buckets of resource group resource-group-1 through the GQL path

Then

- the call is rejected
  - rejected: InsufficientPrivilege

