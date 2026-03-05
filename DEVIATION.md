# Deviation Report: BA-4901

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Client SDK group.create() | Alternative applied | REST `/groups` CRUD routes not yet implemented on server side. Test written with `xfail` marker — will pass once routes are added. |
| Client SDK group.update() | Alternative applied | Same as above — `/groups/{id}` PATCH route missing. Test written with `xfail`. |
| Client SDK group.delete() | Alternative applied | Same as above — `/groups/{id}` DELETE route missing. Test written with `xfail`. |
| Client SDK group.add_users() | Alternative applied | REST `/groups/{id}/members` POST route not yet implemented. Test written with `xfail`. |
| Client SDK group.remove_users() | Alternative applied | REST `/groups/{id}/members` DELETE route not yet implemented. Test written with `xfail`. |
| Group full lifecycle integration | Alternative applied | Depends on group CRUD routes. Test written with `xfail`. Registry-quota portion is testable separately. |
| Client SDK group.get_container_registry_quota() | Alternative applied | Tested via `read_registry_quota` SDK method (matches actual SDK API name). |
| Client SDK group.create_container_registry_quota() | Alternative applied | Tested via `create_registry_quota` SDK method (matches actual SDK API name). |
