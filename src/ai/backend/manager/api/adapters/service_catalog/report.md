## service_catalog

[background](/src/ai/backend/manager/api/adapters/service_catalog/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/service_catalog/adapter.py)

Scenario: incomplete 1 / 2

- built from ops (1)
  - admin_search: representative success ✓ · representative rejection ✓
- direct implementation (1)
  - batch_load_by_ids: success absent · rejection absent (partial_bulk): SCENARIO-GAP

**admin_search**

| scenario | verdict |
|---|---|
| [when a read is filtered by one group among two services of different groups, only the services of that group remain in the answer](#searching-a-group-filter-narrows-the-answer-to-the-services-of-that-group) | answered |
| [when services with one of each status are read filtered by unhealthy, only the unhealthy service comes back](#searching-a-status-equals-filter-keeps-the-services-of-that-status) | answered |
| [when services with one of each status are read filtered by a status in the unhealthy and deregistered list, only the unhealthy and deregistered services come back](#searching-a-status-in-filter-keeps-the-services-of-a-listed-status) | answered |
| [when services with one of each status are read filtered by a status other than unhealthy, only the healthy and deregistered services come back](#searching-a-status-not-equals-filter-drops-the-services-of-that-status) | answered |
| [when services with one of each status are read filtered by a status not in the unhealthy and deregistered list, only the healthy service comes back](#searching-a-status-not-in-filter-drops-the-services-of-a-listed-status) | answered |
| [when eleven services exist and the read names no size, ten services come back and the answer says there is a next page](#searching-omitting-the-page-size-answers-ten-services-and-a-next-page) | answered |
| [when the monitor role reads without a filter, it gets the same answer as the superadmin. This search is a read operation, so the monitor role passes the global role check](#searching-the-monitor-role-counts-every-service-as-the-superadmin-does) | answered |
| [when one of two services holds an endpoint and the superadmin reads without a filter, both are counted once](#searching-the-superadmin-counts-every-service-laid-once) | answered |
| [when a user who is not the superadmin requests a global read, it is rejected for lack of role](#searching-a-user-who-is-not-the-superadmin-may-not-search-services) | rejected |

### admin_search

<a id="searching-a-group-filter-narrows-the-answer-to-the-services-of-that-group"></a>

#### [a-group-filter-narrows-the-answer-to-the-services-of-that-group](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when a read is filtered by one group among two services of different groups, only the services of that group remain in the answer

Given

- two services in different groups and one superadmin
  - Service wanted-1: registered as healthy in the manager group
  - Service other-1: registered as healthy in the agent group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads filtered by the manager group

Then

- only the service of the picked group is left
  - items.id: same as the picked service
  - items.service_group = ['manager']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-equals-filter-keeps-the-services-of-that-status"></a>

#### [a-status-equals-filter-keeps-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when services with one of each status are read filtered by unhealthy, only the unhealthy service comes back

Given

- one service for each status: healthy, unhealthy, deregistered, and one superadmin
  - Service healthy-1: registered as healthy in the manager group
  - Service unhealthy-1: registered as unhealthy in the manager group
  - Service deregistered-1: registered as deregistered in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads filtered by the status unhealthy

Then

- only the services with status unhealthy come back
  - items.id: same as the services seeded in advance with that status
  - items.instance_id = ['unhealthy-1']
  - items.status = [<ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-in-filter-keeps-the-services-of-a-listed-status"></a>

#### [a-status-in-filter-keeps-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when services with one of each status are read filtered by a status in the unhealthy and deregistered list, only the unhealthy and deregistered services come back

Given

- one service for each status: healthy, unhealthy, deregistered, and one superadmin
  - Service healthy-1: registered as healthy in the manager group
  - Service unhealthy-1: registered as unhealthy in the manager group
  - Service deregistered-1: registered as deregistered in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads filtered by one of the statuses unhealthy, deregistered

Then

- only the services with status unhealthy, deregistered come back
  - items.id: same as the services seeded in advance with that status
  - items.instance_id = ['deregistered-1', 'unhealthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.UNHEALTHY: 'unhealthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-not-equals-filter-drops-the-services-of-that-status"></a>

#### [a-status-not-equals-filter-drops-the-services-of-that-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when services with one of each status are read filtered by a status other than unhealthy, only the healthy and deregistered services come back

Given

- one service for each status: healthy, unhealthy, deregistered, and one superadmin
  - Service healthy-1: registered as healthy in the manager group
  - Service unhealthy-1: registered as unhealthy in the manager group
  - Service deregistered-1: registered as deregistered in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads filtered by a status other than unhealthy

Then

- only the services with status healthy, deregistered come back
  - items.id: same as the services seeded in advance with that status
  - items.instance_id = ['deregistered-1', 'healthy-1']
  - items.status = [<ServiceCatalogStatus.DEREGISTERED: 'deregistered'>, <ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-status-not-in-filter-drops-the-services-of-a-listed-status"></a>

#### [a-status-not-in-filter-drops-the-services-of-a-listed-status](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when services with one of each status are read filtered by a status not in the unhealthy and deregistered list, only the healthy service comes back

Given

- one service for each status: healthy, unhealthy, deregistered, and one superadmin
  - Service healthy-1: registered as healthy in the manager group
  - Service unhealthy-1: registered as unhealthy in the manager group
  - Service deregistered-1: registered as deregistered in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads filtered by a status that is none of unhealthy, deregistered

Then

- only the services with status healthy come back
  - items.id: same as the services seeded in advance with that status
  - items.instance_id = ['healthy-1']
  - items.status = [<ServiceCatalogStatus.HEALTHY: 'healthy'>]
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-services-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-services-and-a-next-page](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when eleven services exist and the read names no size, ten services come back and the answer says there is a next page

Given

- 11 services and one superadmin
  - Service wanted-1: registered as healthy in the manager group
  - Service wanted-1: has one endpoint at http://127.0.0.1:8080
  - Service other-1: registered as healthy in the manager group
  - Service other-2: registered as healthy in the manager group
  - Service other-3: registered as healthy in the manager group
  - Service other-4: registered as healthy in the manager group
  - Service other-5: registered as healthy in the manager group
  - Service other-6: registered as healthy in the manager group
  - Service other-7: registered as healthy in the manager group
  - Service other-8: registered as healthy in the manager group
  - Service other-9: registered as healthy in the manager group
  - Service other-10: registered as healthy in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads everything without a filter

Then

- the first page of the default size comes back
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-the-monitor-role-counts-every-service-as-the-superadmin-does"></a>

#### [the-monitor-role-counts-every-service-as-the-superadmin-does](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when the monitor role reads without a filter, it gets the same answer as the superadmin. This search is a read operation, so the monitor role passes the global role check

Given

- 2 services and one monitor
  - Service wanted-1: registered as healthy in the manager group
  - Service wanted-1: has one endpoint at http://127.0.0.1:8080
  - Service other-1: registered as healthy in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads everything without a filter

Then

- every service seeded in advance is counted once, and each whole service comes back
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the service seeded in advance
  - items[0].service_group = 'manager'
  - items[0].instance_id = 'other-1'
  - items[0].display_name = 'other-1'
  - items[0].version = '26.9.0'
  - items[0].labels = {}
  - items[0].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[0].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[0].registered_at: the time this run wrote
  - items[0].last_heartbeat: the time this run wrote
  - items[0].config_hash = ''
  - items[1].id: same as the service seeded in advance
  - items[1].service_group = 'manager'
  - items[1].instance_id = 'wanted-1'
  - items[1].display_name = 'wanted-1'
  - items[1].version = '26.9.0'
  - items[1].labels = {}
  - items[1].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[1].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[1].registered_at: the time this run wrote
  - items[1].last_heartbeat: the time this run wrote
  - items[1].config_hash = ''

<a id="searching-the-superadmin-counts-every-service-laid-once"></a>

#### [the-superadmin-counts-every-service-laid-once](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when one of two services holds an endpoint and the superadmin reads without a filter, both are counted once

Given

- 2 services and one superadmin
  - Service wanted-1: registered as healthy in the manager group
  - Service wanted-1: has one endpoint at http://127.0.0.1:8080
  - Service other-1: registered as healthy in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads everything without a filter

Then

- every service seeded in advance is counted once, and each whole service comes back
  - items.instance_id = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the service seeded in advance
  - items[0].service_group = 'manager'
  - items[0].instance_id = 'other-1'
  - items[0].display_name = 'other-1'
  - items[0].version = '26.9.0'
  - items[0].labels = {}
  - items[0].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[0].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[0].registered_at: the time this run wrote
  - items[0].last_heartbeat: the time this run wrote
  - items[0].config_hash = ''
  - items[1].id: same as the service seeded in advance
  - items[1].service_group = 'manager'
  - items[1].instance_id = 'wanted-1'
  - items[1].display_name = 'wanted-1'
  - items[1].version = '26.9.0'
  - items[1].labels = {}
  - items[1].status = <ServiceCatalogStatus.HEALTHY: 'healthy'>
  - items[1].startup_time = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - items[1].registered_at: the time this run wrote
  - items[1].last_heartbeat: the time this run wrote
  - items[1].config_hash = ''

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-services"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-services](/tests/scenario/bai_scenario/manager/service_catalog/test_searching.py): pass

when a user who is not the superadmin requests a global read, it is rejected for lack of role

Given

- 2 services and one regular user
  - Service wanted-1: registered as healthy in the manager group
  - Service wanted-1: has one endpoint at http://127.0.0.1:8080
  - Service other-1: registered as healthy in the manager group
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ServiceCatalogAdapter.admin_search: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

