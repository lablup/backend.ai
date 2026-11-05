## resource_policy

[background](/src/ai/backend/manager/api/adapters/resource_policy/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/resource_policy/adapter.py)

Scenario: incomplete 6 / 33

- built from ops (33)
  - admin_create_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - admin_create_project_resource_policy: representative success ✓ · representative rejection ✓
  - admin_create_user_resource_policy: representative success ✓ · representative rejection ✓
  - admin_get_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - admin_get_project_resource_policy: representative success ✓ · representative rejection ✓
  - admin_get_user_resource_policy: representative success ✓ · representative rejection ✓
  - admin_search_keypair_resource_policies: representative success ✓ · representative rejection ✓
  - admin_search_project_resource_policies: representative success ✓ · representative rejection ✓
  - admin_search_user_resource_policies: representative success ✓ · representative rejection ✓
  - bulk_get_keypair_resource_policy_ids: representative success ✓ · representative rejection ✓
  - bulk_get_project_resource_policy_ids: representative success ✓ · representative rejection ✓
  - bulk_get_user_resource_policy_ids: representative success ✓ · representative rejection ✓
  - bulk_lookup_keypair_resource_policy_names: representative success ✓ · representative rejection ✓
  - bulk_lookup_project_resource_policy_names: representative success ✓ · representative rejection ✓
  - bulk_lookup_user_resource_policy_names: representative success ✓ · representative rejection ✓
  - get_my_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - get_my_user_resource_policy: representative success ✓ · representative rejection ✓
  - get_project_resource_policy: representative success ✓ · representative rejection ✓
  - lookup_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - lookup_project_resource_policy: representative success ✓ · representative rejection ✓
  - lookup_user_resource_policy: representative success ✓ · representative rejection ✓
  - partial_bulk_purge_keypair_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge_project_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge_user_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update_keypair_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update_project_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update_user_resource_policies: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - purge_project_resource_policy: representative success ✓ · representative rejection ✓
  - purge_user_resource_policy: representative success ✓ · representative rejection ✓
  - update_keypair_resource_policy: representative success ✓ · representative rejection ✓
  - update_project_resource_policy: representative success ✓ · representative rejection ✓
  - update_user_resource_policy: representative success ✓ · representative rejection ✓

**admin_create_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin creates a keypair policy with every slot of one resource set to unlimited, that resource comes back marked unlimited with an empty quantity](#creating-an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited) | answered |
| [when the superadmin creates a keypair policy leaving out every optional entry, the whole node comes back with the omitted fields empty](#creating-leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty) | answered |
| [when the superadmin creates a keypair policy giving every value, the whole node comes back with those values as given](#creating-the-superadmin-creates-a-keypair-policy-giving-every-value) | answered |
| [when a user with the monitor role tries to create a keypair policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only](#creating-a-monitor-may-not-create-a-keypair-policy) | rejected |
| [creating with a name another keypair policy already holds is rejected as a duplicate name](#creating-a-name-another-keypair-policy-already-holds-is-refused) | rejected |
| [when the superadmin tries to create a keypair policy with a priority cap outside the session priority range, the call is rejected on a constraint violation](#creating-a-priority-cap-outside-the-session-range-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a keypair policy, the call is rejected for lacking the role regardless of how much permission the user holds](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy) | rejected |
| [turning permission enforcement off still rejects creating a keypair policy](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy) | rejected |

**admin_create_project_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin creates a project policy giving every value, the whole node comes back with those values as given](#creating-the-superadmin-creates-a-project-policy-giving-every-value) | answered |
| [when a user with the monitor role tries to create a project policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only](#creating-a-monitor-may-not-create-a-project-policy) | rejected |
| [creating with a name another project policy already holds is rejected as a duplicate name](#creating-a-name-another-project-policy-already-holds-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a project policy, the call is rejected for lacking the role regardless of how much permission the user holds](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-project-policy) | rejected |
| [turning permission enforcement off still rejects creating a project policy](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy) | rejected |

**admin_create_user_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin creates a user policy leaving out every optional entry, the whole node comes back with the omitted fields empty](#creating-leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty) | answered |
| [when the superadmin creates a user policy giving every value, the whole node comes back with those values as given](#creating-the-superadmin-creates-a-user-policy-giving-every-value) | answered |
| [when a user with the monitor role tries to create a user policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only](#creating-a-monitor-may-not-create-a-user-policy) | rejected |
| [creating with a name another user policy already holds is rejected as a duplicate name](#creating-a-name-another-user-policy-already-holds-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a user policy, the call is rejected for lacking the role regardless of how much permission the user holds](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-user-policy) | rejected |
| [turning permission enforcement off still rejects creating a user policy](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy) | rejected |

**admin_get_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [one keypair policy exists and the superadmin reads it by name, so the whole policy comes back](#reading-the-superadmin-reads-a-keypair-policy-by-name) | answered |
| [turning permission enforcement off lets a user granted nothing read a keypair policy by name](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy) | answered |
| [when the same keypair policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found](#reading-a-user-granted-nothing-cannot-resolve-a-keypair-policy-name) | rejected |
| [when the superadmin reads a name no keypair policy holds, the call is rejected as no such target, not on a permission problem](#reading-reading-a-keypair-policy-name-nothing-answers-to-is-not-found) | rejected |

**admin_get_project_resource_policy**

| scenario | verdict |
|---|---|
| [one project policy exists and the superadmin reads it by name, so the whole policy comes back](#reading-the-superadmin-reads-a-project-policy-by-name) | answered |
| [turning permission enforcement off lets a user granted nothing read a project policy by name](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy) | answered |
| [when the same project policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found](#reading-a-user-granted-nothing-cannot-resolve-a-project-policy-name) | rejected |
| [when the superadmin reads a name no project policy holds, the call is rejected as no such target, not on a permission problem](#reading-reading-a-project-policy-name-nothing-answers-to-is-not-found) | rejected |

**admin_get_user_resource_policy**

| scenario | verdict |
|---|---|
| [one user policy exists and the superadmin reads it by name, so the whole policy comes back](#reading-the-superadmin-reads-a-user-policy-by-name) | answered |
| [turning permission enforcement off lets a user granted nothing read a user policy by name](#reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy) | answered |
| [when the same user policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found](#reading-a-user-granted-nothing-cannot-resolve-a-user-policy-name) | rejected |
| [when the superadmin reads a name no user policy holds, the call is rejected as no such target, not on a permission problem](#reading-reading-a-user-policy-name-nothing-answers-to-is-not-found) | rejected |

**admin_search_keypair_resource_policies**

| scenario | verdict |
|---|---|
| [when a user with the monitor role searches every policy of the keypair policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too](#searching-a-monitor-finds-every-keypair-policy-like-the-superadmin) | answered |
| [when several keypair policies exist and the superadmin searches with the keypair of a user as the filter, only the policy assigned to that user's keypair comes back](#searching-filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds) | answered |
| [when several policies of the keypair policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back](#searching-filtering-keypair-policy-search-by-name-leaves-that-one) | answered |
| [when several keypair policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those](#searching-the-superadmin-finds-every-keypair-policy) | answered |
| [when a user who is not the superadmin tries to search every policy of the keypair policy kind, the call is rejected for lacking the role](#searching-a-user-who-is-not-the-superadmin-may-not-search-keypair-policy) | rejected |

**admin_search_project_resource_policies**

| scenario | verdict |
|---|---|
| [when a user with the monitor role searches every policy of the project policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too](#searching-a-monitor-finds-every-project-policy-like-the-superadmin) | answered |
| [when several policies of the project policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back](#searching-filtering-project-policy-search-by-name-leaves-that-one) | answered |
| [when several project policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those](#searching-the-superadmin-finds-every-project-policy) | answered |
| [when a user who is not the superadmin tries to search every policy of the project policy kind, the call is rejected for lacking the role](#searching-a-user-who-is-not-the-superadmin-may-not-search-project-policy) | rejected |

**admin_search_user_resource_policies**

| scenario | verdict |
|---|---|
| [when a user with the monitor role searches every policy of the user policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too](#searching-a-monitor-finds-every-user-policy-like-the-superadmin) | answered |
| [when several policies of the user policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back](#searching-filtering-user-policy-search-by-name-leaves-that-one) | answered |
| [when several user policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those](#searching-the-superadmin-finds-every-user-policy) | answered |
| [when a user who is not the superadmin tries to search every policy of the user policy kind, the call is rejected for lacking the role](#searching-a-user-who-is-not-the-superadmin-may-not-search-user-policy) | rejected |

**bulk_get_keypair_resource_policy_ids**

| scenario | verdict |
|---|---|
| [when the superadmin reads one keypair-policy by id, the whole policy comes back for that item](#bulk_reading-the-superadmin-reads-a-keypair-policy-by-id) | answered |
| [a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission](#bulk_reading-a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item) | rejected |

**bulk_get_project_resource_policy_ids**

| scenario | verdict |
|---|---|
| [when the superadmin reads one project-policy by id, the whole policy comes back for that item](#bulk_reading-the-superadmin-reads-a-project-policy-by-id) | answered |
| [a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission](#bulk_reading-a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item) | rejected |

**bulk_get_user_resource_policy_ids**

| scenario | verdict |
|---|---|
| [when the superadmin reads one user-policy by id, the whole policy comes back for that item](#bulk_reading-the-superadmin-reads-a-user-policy-by-id) | answered |
| [a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission](#bulk_reading-a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item) | rejected |

**bulk_lookup_keypair_resource_policy_names**

| scenario | verdict |
|---|---|
| [when the superadmin looks up several ids for a name that exists and one that does not, the keypair-policy id comes back for the name that exists and an empty value for the name that does not](#looking_up-the-superadmin-looks-up-several-keypair-policy-names) | answered |
| [looking up several ids by name without a login context is rejected as user not found](#looking_up-looking-up-several-keypair-policy-names-without-login-is-refused) | rejected |

**bulk_lookup_project_resource_policy_names**

| scenario | verdict |
|---|---|
| [when the superadmin looks up several ids for a name that exists and one that does not, the project-policy id comes back for the name that exists and an empty value for the name that does not](#looking_up-the-superadmin-looks-up-several-project-policy-names) | answered |
| [looking up several ids by name without a login context is rejected as user not found](#looking_up-looking-up-several-project-policy-names-without-login-is-refused) | rejected |

**bulk_lookup_user_resource_policy_names**

| scenario | verdict |
|---|---|
| [when the superadmin looks up several ids for a name that exists and one that does not, the user-policy id comes back for the name that exists and an empty value for the name that does not](#looking_up-the-superadmin-looks-up-several-user-policy-names) | answered |
| [looking up several ids by name without a login context is rejected as user not found](#looking_up-looking-up-several-user-policy-names-without-login-is-refused) | rejected |

**get_my_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [a user granted read on the keypair policy in their own scope reading their own policy gets the whole policy assigned to that user](#reading_own-a-user-granted-read-in-their-own-scope-reads-their-keypair-policy) | answered |
| [a user with one more active keypair, besides the default keypair, holding a different keypair policy reading their own keypair policy gets the policy assigned to the default keypair](#reading_own-among-several-keys-the-default-one-names-the-keypair-policy) | answered |
| [a user whose default keypair is inactive and who has one more active keypair holding a different keypair policy reading their own keypair policy gets the policy assigned to that active keypair](#reading_own-an-inactive-default-key-yields-to-the-active-one) | answered |
| [turning permission enforcement off lets a user granted nothing read their own keypair policy](#reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy) | answered |
| [a user granted nothing reading their own keypair policy is rejected for not enough permission. the call reading their own policy checks the permission instead of only narrowing the scope](#reading_own-a-user-granted-nothing-may-not-read-their-own-keypair-policy) | rejected |
| [a user with no active keypair reading their own keypair policy is rejected because no target answers to it, since no keypair reaches the policy even with the permission](#reading_own-a-user-with-no-active-key-finds-no-keypair-policy-of-their-own) | rejected |

**get_my_user_resource_policy**

| scenario | verdict |
|---|---|
| [a user granted read on the user policy in their own scope reading their own policy gets the whole policy assigned to that user](#reading_own-a-user-granted-read-in-their-own-scope-reads-their-user-policy) | answered |
| [turning permission enforcement off lets a user granted nothing read their own user policy](#reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy) | answered |
| [a user granted nothing reading their own user policy is rejected for not enough permission. the call reading their own policy checks the permission instead of only narrowing the scope](#reading_own-a-user-granted-nothing-may-not-read-their-own-user-policy) | rejected |

**get_project_resource_policy**

| scenario | verdict |
|---|---|
| [a user granted permission to read project resource policies in the project's scope gets the whole policy that project follows](#reading_project_policy-a-user-granted-read-in-the-project-reads-its-resource-policy) | answered |
| [a user granted nothing reading the policy a project follows is rejected because they hold no permission in that project's scope](#reading_project_policy-a-user-granted-nothing-may-not-read-a-projects-resource-policy) | rejected |

**lookup_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin looks up a keypair-policy by name, the id of that policy comes back](#looking_up-the-superadmin-looks-up-a-keypair-policy-by-name) | answered |
| [when the superadmin looks up a name no keypair-policy holds, the call is rejected as no such target](#looking_up-looking-up-a-keypair-policy-name-nothing-answers-to-is-not-found) | rejected |

**lookup_project_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin looks up a project-policy by name, the id of that policy comes back](#looking_up-the-superadmin-looks-up-a-project-policy-by-name) | answered |
| [when the superadmin looks up a name no project-policy holds, the call is rejected as no such target](#looking_up-looking-up-a-project-policy-name-nothing-answers-to-is-not-found) | rejected |

**lookup_user_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin looks up a user-policy by name, the id of that policy comes back](#looking_up-the-superadmin-looks-up-a-user-policy-by-name) | answered |
| [when the superadmin looks up a name no user-policy holds, the call is rejected as no such target](#looking_up-looking-up-a-user-policy-name-nothing-answers-to-is-not-found) | rejected |

**partial_bulk_purge_keypair_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to delete several policies of the keypair policy kind at once gets none deleted and every one in the failed list for not enough permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-keypair-policys) | answered |
| [when the superadmin deletes two unused policies of the keypair policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-keypair-policys-answers-for-the-missing-one) | answered |
| [when the superadmin deletes a still assigned keypair policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced](#partial_bulk_purging-purging-several-keypair-policys-answers-for-the-one-still-held) | answered |

**partial_bulk_purge_project_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to delete several policies of the project policy kind at once gets none deleted and every one in the failed list for not enough permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-project-policys) | answered |
| [when the superadmin deletes two unused policies of the project policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-project-policys-answers-for-the-missing-one) | answered |
| [when the superadmin deletes a still assigned project policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced](#partial_bulk_purging-purging-several-project-policys-answers-for-the-one-still-held) | answered |

**partial_bulk_purge_user_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to delete several policies of the user policy kind at once gets none deleted and every one in the failed list for not enough permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-user-policys) | answered |
| [when the superadmin deletes two unused policies of the user policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-user-policys-answers-for-the-missing-one) | answered |
| [when the superadmin deletes a still assigned user policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced](#partial_bulk_purging-purging-several-user-policys-answers-for-the-one-still-held) | answered |

**partial_bulk_update_keypair_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to edit several policies of the keypair policy kind at once gets none edited and every one in the failed list for not enough permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-keypair-policys) | answered |
| [when the superadmin changes one limit of several policies of the keypair policy kind at once, they all come back with only that limit at the new value and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-keypair-policys-at-once) | answered |

**partial_bulk_update_project_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to edit several policies of the project policy kind at once gets none edited and every one in the failed list for not enough permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-project-policys) | answered |
| [when the superadmin changes one limit of several policies of the project policy kind at once, they all come back with only that limit at the new value and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-project-policys-at-once) | answered |

**partial_bulk_update_user_resource_policies**

| scenario | verdict |
|---|---|
| [a user granted nothing trying to edit several policies of the user policy kind at once gets none edited and every one in the failed list for not enough permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-user-policys) | answered |
| [when the superadmin changes one limit of several policies of the user policy kind at once, they all come back with only that limit at the new value and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-user-policys-at-once) | answered |

**purge_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin deletes an unused keypair policy, the deleted name comes back and searching right after finds nothing](#retiring-the-superadmin-purges-a-keypair-policy-nobody-holds) | answered |
| [when the same keypair policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found](#retiring-a-user-granted-nothing-may-not-purge-a-keypair-policy) | rejected |
| [when the superadmin tries to delete a name no keypair policy holds, the call is rejected as no such target, not on a permission problem](#retiring-purging-a-keypair-policy-name-nothing-answers-to-is-not-found) | rejected |
| [when the superadmin tries to delete a keypair policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec](#retiring-purging-a-keypair-policy-still-held-is-refused) | rejected |

**purge_project_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin deletes an unused project policy, the deleted name comes back and searching right after finds nothing](#retiring-the-superadmin-purges-a-project-policy-nobody-holds) | answered |
| [when the same project policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found](#retiring-a-user-granted-nothing-may-not-purge-a-project-policy) | rejected |
| [when the superadmin tries to delete a name no project policy holds, the call is rejected as no such target, not on a permission problem](#retiring-purging-a-project-policy-name-nothing-answers-to-is-not-found) | rejected |
| [when the superadmin tries to delete a project policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec](#retiring-purging-a-project-policy-still-held-is-refused) | rejected |

**purge_user_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin deletes an unused user policy, the deleted name comes back and searching right after finds nothing](#retiring-the-superadmin-purges-a-user-policy-nobody-holds) | answered |
| [when the same user policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found](#retiring-a-user-granted-nothing-may-not-purge-a-user-policy) | rejected |
| [when the superadmin tries to delete a name no user policy holds, the call is rejected as no such target, not on a permission problem](#retiring-purging-a-user-policy-name-nothing-answers-to-is-not-found) | rejected |
| [when the superadmin tries to delete a user policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec](#retiring-purging-a-user-policy-still-held-is-refused) | rejected |

**update_keypair_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin clears a non-nullable entry of a keypair policy, the request is ignored and the node comes back with nothing changed](#editing-clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was) | answered |
| [when the superadmin clears the nullable entry of a keypair policy that holds a value, the node comes back with that entry empty](#editing-clearing-a-nullable-value-of-a-keypair-policy-empties-it) | answered |
| [when the superadmin names a keypair policy and gives no value, the node comes back with nothing changed](#editing-giving-no-value-changes-nothing-of-a-keypair-policy) | answered |
| [one keypair policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was](#editing-the-superadmin-changes-one-limit-of-a-keypair-policy) | answered |
| [when the same keypair policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found](#editing-a-user-granted-nothing-may-not-edit-a-keypair-policy) | rejected |
| [when the superadmin tries to edit a name no keypair policy holds, the call is rejected as no such target, not on a permission problem](#editing-editing-a-keypair-policy-name-nothing-answers-to-is-not-found) | rejected |
| [when the superadmin tries to move the priority cap of a keypair policy outside the session priority range, the call is rejected on a constraint violation](#editing-moving-the-priority-cap-outside-the-session-range-is-refused) | rejected |

**update_project_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin clears a non-nullable entry of a project policy, the request is ignored and the node comes back with nothing changed](#editing-clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was) | answered |
| [when the superadmin names a project policy and gives no value, the node comes back with nothing changed](#editing-giving-no-value-changes-nothing-of-a-project-policy) | answered |
| [one project policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was](#editing-the-superadmin-changes-one-limit-of-a-project-policy) | answered |
| [when the same project policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found](#editing-a-user-granted-nothing-may-not-edit-a-project-policy) | rejected |
| [when the superadmin tries to edit a name no project policy holds, the call is rejected as no such target, not on a permission problem](#editing-editing-a-project-policy-name-nothing-answers-to-is-not-found) | rejected |

**update_user_resource_policy**

| scenario | verdict |
|---|---|
| [when the superadmin clears a non-nullable entry of a user policy, the request is ignored and the node comes back with nothing changed](#editing-clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was) | answered |
| [when the superadmin clears the nullable entry of a user policy that holds a value, the node comes back with that entry empty](#editing-clearing-a-nullable-value-of-a-user-policy-empties-it) | answered |
| [when the superadmin names a user policy and gives no value, the node comes back with nothing changed](#editing-giving-no-value-changes-nothing-of-a-user-policy) | answered |
| [one user policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was](#editing-the-superadmin-changes-one-limit-of-a-user-policy) | answered |
| [when the same user policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found](#editing-a-user-granted-nothing-may-not-edit-a-user-policy) | rejected |
| [when the superadmin tries to edit a name no user policy holds, the call is rejected as no such target, not on a permission problem](#editing-editing-a-user-policy-name-nothing-answers-to-is-not-found) | rejected |

### admin_create_keypair_resource_policy

<a id="creating-an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited"></a>

#### [an-unlimited-slot-of-a-keypair-policy-comes-back-marked-unlimited](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a keypair policy with every slot of one resource set to unlimited, that resource comes back marked unlimited with an empty quantity

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy the cpu slot set to unlimited

Then

- the whole keypair policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', None, True)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty"></a>

#### [leaving-the-optional-values-out-of-a-keypair-policy-leaves-them-empty](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a keypair policy leaving out every optional entry, the whole node comes back with the omitted fields empty

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy the pending session count, the priority cap and the pending resource slots left out

Then

- the whole keypair policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-the-superadmin-creates-a-keypair-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-keypair-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a keypair policy giving every value, the whole node comes back with those values as given

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy all values given

Then

- the whole keypair policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.LIMITED: 'LIMITED'>
  - total_resource_slots = [('cpu', Decimal('4'), False)]
  - max_session_lifetime = 3600
  - max_concurrent_sessions = 5
  - max_pending_session_count = 2
  - max_priority = 10
  - max_pending_session_resource_slots = [('cpu', Decimal('2'), False)]
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 600
  - allowed_vfolder_hosts = [('local:volume1', ['mount-in-session'])]

<a id="creating-a-monitor-may-not-create-a-keypair-policy"></a>

#### [a-monitor-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user with the monitor role tries to create a keypair policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only

Given

- one unused keypair policy and one monitor
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-a-name-another-keypair-policy-already-holds-is-refused"></a>

#### [a-name-another-keypair-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

creating with a name another keypair policy already holds is rejected as a duplicate name

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy with an existing name

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="creating-a-priority-cap-outside-the-session-range-is-refused"></a>

#### [a-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin tries to create a keypair policy with a priority cap outside the session priority range, the call is rejected on a constraint violation

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy the priority cap set to a value outside the session priority range

Then

- the call is rejected
  - rejected: CheckConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user who is not the superadmin tries to create a keypair policy, the call is rejected for lacking the role regardless of how much permission the user holds

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

turning permission enforcement off still rejects creating a keypair policy

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_create_keypair_resource_policy: user-1 creates the keypair policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_create_project_resource_policy

<a id="creating-the-superadmin-creates-a-project-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-project-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a project policy giving every value, the whole node comes back with those values as given

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1 creates the project policy all values given

Then

- the whole project policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - max_vfolder_count = 20
  - max_quota_scope_size = ('1073741824', '1g')
  - max_network_count = 5

<a id="creating-a-monitor-may-not-create-a-project-policy"></a>

#### [a-monitor-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user with the monitor role tries to create a project policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only

Given

- one unused project policy and one monitor
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1 creates the project policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-a-name-another-project-policy-already-holds-is-refused"></a>

#### [a-name-another-project-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

creating with a name another project policy already holds is rejected as a duplicate name

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1 creates the project policy with an existing name

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-project-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user who is not the superadmin tries to create a project policy, the call is rejected for lacking the role regardless of how much permission the user holds

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1 creates the project policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

turning permission enforcement off still rejects creating a project policy

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_create_project_resource_policy: user-1 creates the project policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_create_user_resource_policy

<a id="creating-leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty"></a>

#### [leaving-the-optional-values-out-of-a-user-policy-leaves-them-empty](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a user policy leaving out every optional entry, the whole node comes back with the omitted fields empty

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy the concurrent login count left out

Then

- the whole user policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - max_vfolder_count = 20
  - max_concurrent_logins = None
  - max_quota_scope_size = ('1073741824', '1g')
  - max_session_count_per_model_session = 4
  - max_customized_image_count = 2

<a id="creating-the-superadmin-creates-a-user-policy-giving-every-value"></a>

#### [the-superadmin-creates-a-user-policy-giving-every-value](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when the superadmin creates a user policy giving every value, the whole node comes back with those values as given

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy all values given

Then

- the whole user policy just created comes back
  - id = 'fresh-policy'
  - name = 'fresh-policy'
  - created_at: the time this run wrote
  - max_vfolder_count = 20
  - max_concurrent_logins = 3
  - max_quota_scope_size = ('1073741824', '1g')
  - max_session_count_per_model_session = 4
  - max_customized_image_count = 2

<a id="creating-a-monitor-may-not-create-a-user-policy"></a>

#### [a-monitor-may-not-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user with the monitor role tries to create a user policy, the call is rejected for lacking the role. the superadmin check allows the monitor reads only

Given

- one unused user policy and one monitor
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-a-name-another-user-policy-already-holds-is-refused"></a>

#### [a-name-another-user-policy-already-holds-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

creating with a name another user policy already holds is rejected as a duplicate name

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy with an existing name

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-user-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

when a user who is not the superadmin tries to create a user policy, the call is rejected for lacking the role regardless of how much permission the user holds

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_creating.py): pass

turning permission enforcement off still rejects creating a user policy

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_create_user_resource_policy: user-1 creates the user policy all values given

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_get_keypair_resource_policy

<a id="reading-the-superadmin-reads-a-keypair-policy-by-name"></a>

#### [the-superadmin-reads-a-keypair-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

one keypair policy exists and the superadmin reads it by name, so the whole policy comes back

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1 reads keypair-policy-2 by name

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

turning permission enforcement off lets a user granted nothing read a keypair policy by name

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1 reads keypair-policy-2 by name

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading-a-user-granted-nothing-cannot-resolve-a-keypair-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-keypair-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the same keypair policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1 reads keypair-policy-2 by name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading-reading-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the superadmin reads a name no keypair policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_get_keypair_resource_policy: user-1 reads nobody by name

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_get_project_resource_policy

<a id="reading-the-superadmin-reads-a-project-policy-by-name"></a>

#### [the-superadmin-reads-a-project-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

one project policy exists and the superadmin reads it by name, so the whole policy comes back

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1 reads project-policy-1 by name

Then

- the whole project policy seeded in advance comes back
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

turning permission enforcement off lets a user granted nothing read a project policy by name

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1 reads project-policy-1 by name

Then

- the whole project policy seeded in advance comes back
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading-a-user-granted-nothing-cannot-resolve-a-project-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-project-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the same project policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1 reads project-policy-1 by name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading-reading-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the superadmin reads a name no project policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_get_project_resource_policy: user-1 reads nobody by name

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_get_user_resource_policy

<a id="reading-the-superadmin-reads-a-user-policy-by-name"></a>

#### [the-superadmin-reads-a-user-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

one user policy exists and the superadmin reads it by name, so the whole policy comes back

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1 reads user-policy-2 by name

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading-turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

turning permission enforcement off lets a user granted nothing read a user policy by name

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1 reads user-policy-2 by name

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading-a-user-granted-nothing-cannot-resolve-a-user-policy-name"></a>

#### [a-user-granted-nothing-cannot-resolve-a-user-policy-name](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the same user policy exists and a user granted nothing reads it by name, the call is rejected because the policy cannot be found

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1 reads user-policy-2 by name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading-reading-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [reading-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_reading.py): pass

when the superadmin reads a name no user policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_get_user_resource_policy: user-1 reads nobody by name

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_search_keypair_resource_policies

<a id="searching-a-monitor-finds-every-keypair-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-keypair-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user with the monitor role searches every policy of the keypair policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too

Given

- 3 policies of the keypair policy kind and one monitor with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Keypair policy wanted-1: up to 5 concurrent sessions
  - Keypair policy other-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1 searches everything without a filter

Then

- every keypair policy seeded in advance comes back, and only those
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds"></a>

#### [filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several keypair policies exist and the superadmin searches with the keypair of a user as the filter, only the policy assigned to that user's keypair comes back

Given

- 3 policies of the keypair policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy wanted-1: up to 5 concurrent sessions
  - Keypair policy other-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1 searches with their own keypair filter

Then

- only the one keypair policy assigned to the caller's keypair comes back
  - items = ['keypair-policy-1']
  - total_count = 1

<a id="searching-filtering-keypair-policy-search-by-name-leaves-that-one"></a>

#### [filtering-keypair-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several policies of the keypair policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back

Given

- 3 policies of the keypair policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy wanted-1: up to 5 concurrent sessions
  - Keypair policy other-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1 searches with the name wanted-1 filter

Then

- only the one keypair policy the filter names comes back
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-keypair-policy"></a>

#### [the-superadmin-finds-every-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several keypair policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those

Given

- 3 policies of the keypair policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy wanted-1: up to 5 concurrent sessions
  - Keypair policy other-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1 searches everything without a filter

Then

- every keypair policy seeded in advance comes back, and only those
  - items = ['keypair-policy-1', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-keypair-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user who is not the superadmin tries to search every policy of the keypair policy kind, the call is rejected for lacking the role

Given

- 3 policies of the keypair policy kind and one user with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy wanted-1: up to 5 concurrent sessions
  - Keypair policy other-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.admin_search_keypair_resource_policies: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_project_resource_policies

<a id="searching-a-monitor-finds-every-project-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-project-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user with the monitor role searches every policy of the project policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too

Given

- 3 policies of the project policy kind and one monitor with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Project resource policy wanted-1: up to 10 folders per project
  - Project resource policy other-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1 searches everything without a filter

Then

- every project policy seeded in advance comes back, and only those
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-project-policy-search-by-name-leaves-that-one"></a>

#### [filtering-project-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several policies of the project policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back

Given

- 3 policies of the project policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy wanted-1: up to 10 folders per project
  - Project resource policy other-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1 searches with the name wanted-1 filter

Then

- only the one project policy the filter names comes back
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-project-policy"></a>

#### [the-superadmin-finds-every-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several project policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those

Given

- 3 policies of the project policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy wanted-1: up to 10 folders per project
  - Project resource policy other-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1 searches everything without a filter

Then

- every project policy seeded in advance comes back, and only those
  - items = ['default', 'other-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-project-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user who is not the superadmin tries to search every policy of the project policy kind, the call is rejected for lacking the role

Given

- 3 policies of the project policy kind and one user with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy wanted-1: up to 10 folders per project
  - Project resource policy other-1: up to 10 folders per project

When

- ResourcePolicyAdapter.admin_search_project_resource_policies: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_user_resource_policies

<a id="searching-a-monitor-finds-every-user-policy-like-the-superadmin"></a>

#### [a-monitor-finds-every-user-policy-like-the-superadmin](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user with the monitor role searches every policy of the user policy kind, the same response comes back as for the superadmin, because the superadmin check allows the monitor reads too

Given

- 3 policies of the user policy kind and one monitor with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - User resource policy wanted-1: up to 10 folders per user
  - User resource policy other-1: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1 searches everything without a filter

Then

- every user policy seeded in advance comes back, and only those
  - items = ['other-1', 'user-policy-1', 'wanted-1']
  - total_count = 3

<a id="searching-filtering-user-policy-search-by-name-leaves-that-one"></a>

#### [filtering-user-policy-search-by-name-leaves-that-one](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several policies of the user policy kind with different names exist and the superadmin searches with one of those names as the filter, only the policy of that name comes back

Given

- 3 policies of the user policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy wanted-1: up to 10 folders per user
  - User resource policy other-1: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1 searches with the name wanted-1 filter

Then

- only the one user policy the filter names comes back
  - items = ['wanted-1']
  - total_count = 1

<a id="searching-the-superadmin-finds-every-user-policy"></a>

#### [the-superadmin-finds-every-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when several user policy policies exist and the superadmin searches everything without a filter, every policy seeded in advance comes back and only those

Given

- 3 policies of the user policy kind and one superadmin with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy wanted-1: up to 10 folders per user
  - User resource policy other-1: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1 searches everything without a filter

Then

- every user policy seeded in advance comes back, and only those
  - items = ['other-1', 'user-policy-1', 'wanted-1']
  - total_count = 3

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-user-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_searching.py): pass

when a user who is not the superadmin tries to search every policy of the user policy kind, the call is rejected for lacking the role

Given

- 3 policies of the user policy kind and one user with one of them assigned
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy wanted-1: up to 10 folders per user
  - User resource policy other-1: up to 10 folders per user

When

- ResourcePolicyAdapter.admin_search_user_resource_policies: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### bulk_get_keypair_resource_policy_ids

<a id="bulk_reading-the-superadmin-reads-a-keypair-policy-by-id"></a>

#### [the-superadmin-reads-a-keypair-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

when the superadmin reads one keypair-policy by id, the whole policy comes back for that item

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.bulk_get_keypair_resource_policy_ids: user-1 reads several by the id of keypair-policy-2

Then

- the whole policy seeded in advance comes back for the item asked
  - len(items) = 1
  - items[0].id = 'keypair-policy-2'
  - items[0].name = 'keypair-policy-2'
  - items[0].created_at: the time this run wrote
  - items[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - items[0].total_resource_slots = []
  - items[0].max_session_lifetime = 0
  - items[0].max_concurrent_sessions = 5
  - items[0].max_pending_session_count = None
  - items[0].max_priority = None
  - items[0].max_pending_session_resource_slots = None
  - items[0].max_concurrent_sftp_sessions = 1
  - items[0].max_containers_per_session = 1
  - items[0].idle_timeout = 3600
  - items[0].allowed_vfolder_hosts = []

<a id="bulk_reading-a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-keypair-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.bulk_get_keypair_resource_policy_ids: user-1 reads several by the id of keypair-policy-2

Then

- the item asked is rejected for not enough permission
  - rejected: NotEnoughPermission

### bulk_get_project_resource_policy_ids

<a id="bulk_reading-the-superadmin-reads-a-project-policy-by-id"></a>

#### [the-superadmin-reads-a-project-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

when the superadmin reads one project-policy by id, the whole policy comes back for that item

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.bulk_get_project_resource_policy_ids: user-1 reads several by the id of project-policy-1

Then

- the whole policy seeded in advance comes back for the item asked
  - len(items) = 1
  - items[0].id = 'project-policy-1'
  - items[0].name = 'project-policy-1'
  - items[0].created_at: the time this run wrote
  - items[0].max_vfolder_count = 10
  - items[0].max_quota_scope_size = ('-1', '-1')
  - items[0].max_network_count = 3

<a id="bulk_reading-a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-project-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.bulk_get_project_resource_policy_ids: user-1 reads several by the id of project-policy-1

Then

- the item asked is rejected for not enough permission
  - rejected: NotEnoughPermission

### bulk_get_user_resource_policy_ids

<a id="bulk_reading-the-superadmin-reads-a-user-policy-by-id"></a>

#### [the-superadmin-reads-a-user-policy-by-id](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

when the superadmin reads one user-policy by id, the whole policy comes back for that item

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.bulk_get_user_resource_policy_ids: user-1 reads several by the id of user-policy-2

Then

- the whole policy seeded in advance comes back for the item asked
  - len(items) = 1
  - items[0].id = 'user-policy-2'
  - items[0].name = 'user-policy-2'
  - items[0].created_at: the time this run wrote
  - items[0].max_vfolder_count = 10
  - items[0].max_concurrent_logins = None
  - items[0].max_quota_scope_size = ('-1', '-1')
  - items[0].max_session_count_per_model_session = 10
  - items[0].max_customized_image_count = 3

<a id="bulk_reading-a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item"></a>

#### [a-user-granted-nothing-reading-a-user-policy-by-id-is-refused-per-item](/tests/scenario/bai_scenario/manager/resource_policy/test_bulk_reading.py): pass

a user granted nothing reading one policy by id is not rejected as a call, and that item is rejected for not enough permission

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.bulk_get_user_resource_policy_ids: user-1 reads several by the id of user-policy-2

Then

- the item asked is rejected for not enough permission
  - rejected: NotEnoughPermission

### bulk_lookup_keypair_resource_policy_names

<a id="looking_up-the-superadmin-looks-up-several-keypair-policy-names"></a>

#### [the-superadmin-looks-up-several-keypair-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up several ids for a name that exists and one that does not, the keypair-policy id comes back for the name that exists and an empty value for the name that does not

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.bulk_lookup_keypair_resource_policy_names: user-1 looks up several ids for keypair-policy-2 and nobody

Then

- the id of that policy comes back for the name that exists, and an empty value for the name that does not
  - [0]: same as the id of the policy seeded in advance
  - [1] = None

<a id="looking_up-looking-up-several-keypair-policy-names-without-login-is-refused"></a>

#### [looking-up-several-keypair-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

looking up several ids by name without a login context is rejected as user not found

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.bulk_lookup_keypair_resource_policy_names: without a login context, looks up several ids for keypair-policy-2

Then

- the call is rejected
  - rejected: UserNotFound

### bulk_lookup_project_resource_policy_names

<a id="looking_up-the-superadmin-looks-up-several-project-policy-names"></a>

#### [the-superadmin-looks-up-several-project-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up several ids for a name that exists and one that does not, the project-policy id comes back for the name that exists and an empty value for the name that does not

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.bulk_lookup_project_resource_policy_names: user-1 looks up several ids for project-policy-1 and nobody

Then

- the id of that policy comes back for the name that exists, and an empty value for the name that does not
  - [0]: same as the id of the policy seeded in advance
  - [1] = None

<a id="looking_up-looking-up-several-project-policy-names-without-login-is-refused"></a>

#### [looking-up-several-project-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

looking up several ids by name without a login context is rejected as user not found

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.bulk_lookup_project_resource_policy_names: without a login context, looks up several ids for project-policy-1

Then

- the call is rejected
  - rejected: UserNotFound

### bulk_lookup_user_resource_policy_names

<a id="looking_up-the-superadmin-looks-up-several-user-policy-names"></a>

#### [the-superadmin-looks-up-several-user-policy-names](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up several ids for a name that exists and one that does not, the user-policy id comes back for the name that exists and an empty value for the name that does not

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.bulk_lookup_user_resource_policy_names: user-1 looks up several ids for user-policy-2 and nobody

Then

- the id of that policy comes back for the name that exists, and an empty value for the name that does not
  - [0]: same as the id of the policy seeded in advance
  - [1] = None

<a id="looking_up-looking-up-several-user-policy-names-without-login-is-refused"></a>

#### [looking-up-several-user-policy-names-without-login-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

looking up several ids by name without a login context is rejected as user not found

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.bulk_lookup_user_resource_policy_names: without a login context, looks up several ids for user-policy-2

Then

- the call is rejected
  - rejected: UserNotFound

### get_my_keypair_resource_policy

<a id="reading_own-a-user-granted-read-in-their-own-scope-reads-their-keypair-policy"></a>

#### [a-user-granted-read-in-their-own-scope-reads-their-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user granted read on the keypair policy in their own scope reading their own policy gets the whole policy assigned to that user

Given

- one user with a keypair policy assigned, allowed to read that policy in their own scope
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare the role assignment that grants read permission on keypair_resource_policy in the user's own scope
    - Role policy-reader-1: applies only within the scope it is granted in
    - Role policy-reader-1: READ allowed on every keypair_resource_policy
    - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-among-several-keys-the-default-one-names-the-keypair-policy"></a>

#### [among-several-keys-the-default-one-names-the-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user with one more active keypair, besides the default keypair, holding a different keypair policy reading their own keypair policy gets the policy assigned to the default keypair

Given

- a user with one more active keypair, besides the default keypair, that holds a different keypair policy, and with read permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy other-1: up to 5 concurrent sessions
  - regular user user-1: One more active keypair with the other-1 policy assigned
  - Prepare the role assignment that grants read permission on keypair_resource_policy in the user's own scope
    - Role policy-reader-1: applies only within the scope it is granted in
    - Role policy-reader-1: READ allowed on every keypair_resource_policy
    - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-an-inactive-default-key-yields-to-the-active-one"></a>

#### [an-inactive-default-key-yields-to-the-active-one](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user whose default keypair is inactive and who has one more active keypair holding a different keypair policy reading their own keypair policy gets the policy assigned to that active keypair

Given

- a user whose default keypair is inactive and who has one more active keypair holding a different keypair policy, and with read permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy other-1: up to 5 concurrent sessions
  - regular user user-1: One more active keypair with the other-1 policy assigned
  - Prepare the role assignment that grants read permission on keypair_resource_policy in the user's own scope
    - Role policy-reader-1: applies only within the scope it is granted in
    - Role policy-reader-1: READ allowed on every keypair_resource_policy
    - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the whole keypair policy seeded in advance comes back
  - id = 'other-1'
  - name = 'other-1'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

turning permission enforcement off lets a user granted nothing read their own keypair policy

Given

- one user with a keypair policy assigned and no permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-1'
  - name = 'keypair-policy-1'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="reading_own-a-user-granted-nothing-may-not-read-their-own-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-read-their-own-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user granted nothing reading their own keypair policy is rejected for not enough permission. the call reading their own policy checks the permission instead of only narrowing the scope

Given

- one user with a keypair policy assigned and no permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_own-a-user-with-no-active-key-finds-no-keypair-policy-of-their-own"></a>

#### [a-user-with-no-active-key-finds-no-keypair-policy-of-their-own](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user with no active keypair reading their own keypair policy is rejected because no target answers to it, since no keypair reaches the policy even with the permission

Given

- a user with no active keypair, allowed to read keypair policies in their own scope
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare the role assignment that grants read permission on keypair_resource_policy in the user's own scope
    - Role policy-reader-1: applies only within the scope it is granted in
    - Role policy-reader-1: READ allowed on every keypair_resource_policy
    - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_my_keypair_resource_policy: user-1 reads their own keypair policy

Then

- the call is rejected
  - rejected: KeypairResourcePolicyNotFound

### get_my_user_resource_policy

<a id="reading_own-a-user-granted-read-in-their-own-scope-reads-their-user-policy"></a>

#### [a-user-granted-read-in-their-own-scope-reads-their-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user granted read on the user policy in their own scope reading their own policy gets the whole policy assigned to that user

Given

- one user with a user policy assigned, allowed to read that policy in their own scope
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare the role assignment that grants read permission on user_resource_policy in the user's own scope
    - Role policy-reader-1: applies only within the scope it is granted in
    - Role policy-reader-1: READ allowed on every user_resource_policy
    - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1 reads their own user policy

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-1'
  - name = 'user-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading_own-turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read-their-own-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

turning permission enforcement off lets a user granted nothing read their own user policy

Given

- one user with a user policy assigned and no permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1 reads their own user policy

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-1'
  - name = 'user-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="reading_own-a-user-granted-nothing-may-not-read-their-own-user-policy"></a>

#### [a-user-granted-nothing-may-not-read-their-own-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_own.py): pass

a user granted nothing reading their own user policy is rejected for not enough permission. the call reading their own policy checks the permission instead of only narrowing the scope

Given

- one user with a user policy assigned and no permission
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.get_my_user_resource_policy: user-1 reads their own user policy

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_project_resource_policy

<a id="reading_project_policy-a-user-granted-read-in-the-project-reads-its-resource-policy"></a>

#### [a-user-granted-read-in-the-project-reads-its-resource-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_project_policy.py): pass

a user granted permission to read project resource policies in the project's scope gets the whole policy that project follows

Given

- one project and one regular user granted permission to read project resource policies in that project's scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role policy-reader-1: applies only within the scope it is granted in
  - Role policy-reader-1: READ allowed on every project_resource_policy
  - regular user user-1: holds Role policy-reader-1

When

- ResourcePolicyAdapter.get_project_resource_policy: user-1 reads the policy of the project team-1

Then

- the whole project policy that project follows comes back
  - id = 'default'
  - name = 'default'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="reading_project_policy-a-user-granted-nothing-may-not-read-a-projects-resource-policy"></a>

#### [a-user-granted-nothing-may-not-read-a-projects-resource-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_reading_project_policy.py): pass

a user granted nothing reading the policy a project follows is rejected because they hold no permission in that project's scope

Given

- one project and one regular user granted nothing
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.get_project_resource_policy: user-1 reads the policy of the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### lookup_keypair_resource_policy

<a id="looking_up-the-superadmin-looks-up-a-keypair-policy-by-name"></a>

#### [the-superadmin-looks-up-a-keypair-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a keypair-policy by name, the id of that policy comes back

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.lookup_keypair_resource_policy: user-1 looks up the id of keypair-policy-2

Then

- the id of that policy comes back
  - id: same as the id of the policy seeded in advance

<a id="looking_up-looking-up-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a name no keypair-policy holds, the call is rejected as no such target

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.lookup_keypair_resource_policy: user-1 looks up the id of nobody

Then

- the call is rejected
  - rejected: EntityNotFoundError

### lookup_project_resource_policy

<a id="looking_up-the-superadmin-looks-up-a-project-policy-by-name"></a>

#### [the-superadmin-looks-up-a-project-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a project-policy by name, the id of that policy comes back

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.lookup_project_resource_policy: user-1 looks up the id of project-policy-1

Then

- the id of that policy comes back
  - id: same as the id of the policy seeded in advance

<a id="looking_up-looking-up-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a name no project-policy holds, the call is rejected as no such target

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.lookup_project_resource_policy: user-1 looks up the id of nobody

Then

- the call is rejected
  - rejected: EntityNotFoundError

### lookup_user_resource_policy

<a id="looking_up-the-superadmin-looks-up-a-user-policy-by-name"></a>

#### [the-superadmin-looks-up-a-user-policy-by-name](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a user-policy by name, the id of that policy comes back

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.lookup_user_resource_policy: user-1 looks up the id of user-policy-2

Then

- the id of that policy comes back
  - id: same as the id of the policy seeded in advance

<a id="looking_up-looking-up-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [looking-up-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_looking_up.py): pass

when the superadmin looks up a name no user-policy holds, the call is rejected as no such target

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.lookup_user_resource_policy: user-1 looks up the id of nobody

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_purge_keypair_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-keypair-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-keypair-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

a user granted nothing trying to delete several policies of the keypair policy kind at once gets none deleted and every one in the failed list for not enough permission

Given

- 2 unused policies of the keypair policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy target-1: up to 5 concurrent sessions
  - Keypair policy target-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1 deletes 2 policies of the keypair policy kind at once

Then

- no keypair policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-keypair-policys-answers-for-the-missing-one"></a>

#### [purging-several-keypair-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes two unused policies of the keypair policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- 2 unused policies of the keypair policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy target-1: up to 5 concurrent sessions
  - Keypair policy target-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1 deletes 2 policies of the keypair policy kind and one unknown id at once

Then

- every target keypair policy comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 5
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[1].total_resource_slots = []
  - successes[1].max_session_lifetime = 0
  - successes[1].max_concurrent_sessions = 5
  - successes[1].max_pending_session_count = None
  - successes[1].max_priority = None
  - successes[1].max_pending_session_resource_slots = None
  - successes[1].max_concurrent_sftp_sessions = 1
  - successes[1].max_containers_per_session = 1
  - successes[1].idle_timeout = 3600
  - successes[1].allowed_vfolder_hosts = []
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-purging-several-keypair-policys-answers-for-the-one-still-held"></a>

#### [purging-several-keypair-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes a still assigned keypair policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced

Given

- 1 unused policies of the keypair policy kind and one superadmin, with the keypair policy assigned to that user also among the targets
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy target-1: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.partial_bulk_purge_keypair_resource_policies: user-1 deletes 2 policies of the keypair policy kind at once

Then

- the unused keypair policy comes back in the processed list and the one still assigned comes back in the failed list because it is still referenced
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 5
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - failed count = 1
  - failed[0].id: same as the id of the policy assigned to the caller
  - failed[0].message: a reason containing 'Foreign key'

### partial_bulk_purge_project_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-project-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-project-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

a user granted nothing trying to delete several policies of the project policy kind at once gets none deleted and every one in the failed list for not enough permission

Given

- 2 unused policies of the project policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy target-1: up to 10 folders per project
  - Project resource policy target-2: up to 10 folders per project

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1 deletes 2 policies of the project policy kind at once

Then

- no project policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-project-policys-answers-for-the-missing-one"></a>

#### [purging-several-project-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes two unused policies of the project policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- 2 unused policies of the project policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy target-1: up to 10 folders per project
  - Project resource policy target-2: up to 10 folders per project

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1 deletes 2 policies of the project policy kind and one unknown id at once

Then

- every target project policy comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 10
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].max_vfolder_count = 10
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_network_count = 3
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-purging-several-project-policys-answers-for-the-one-still-held"></a>

#### [purging-several-project-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes a still assigned project policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced

Given

- 1 unused policies of the project policy kind and one superadmin, with the project policy assigned to that user also among the targets
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy target-1: up to 10 folders per project

When

- ResourcePolicyAdapter.partial_bulk_purge_project_resource_policies: user-1 deletes 2 policies of the project policy kind at once

Then

- the unused project policy comes back in the processed list and the one still assigned comes back in the failed list because it is still referenced
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 10
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - failed count = 1
  - failed[0].id: same as the id of the policy assigned to the caller
  - failed[0].message: a reason containing 'Foreign key'

### partial_bulk_purge_user_resource_policies

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-user-policys"></a>

#### [a-user-granted-nothing-purges-none-of-several-user-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

a user granted nothing trying to delete several policies of the user policy kind at once gets none deleted and every one in the failed list for not enough permission

Given

- 2 unused policies of the user policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy target-1: up to 10 folders per user
  - User resource policy target-2: up to 10 folders per user

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1 deletes 2 policies of the user policy kind at once

Then

- no user policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-user-policys-answers-for-the-missing-one"></a>

#### [purging-several-user-policys-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes two unused policies of the user policy kind and one unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- 2 unused policies of the user policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy target-1: up to 10 folders per user
  - User resource policy target-2: up to 10 folders per user

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1 deletes 2 policies of the user policy kind and one unknown id at once

Then

- every target user policy comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 10
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].max_vfolder_count = 10
  - successes[1].max_concurrent_logins = None
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_session_count_per_model_session = 10
  - successes[1].max_customized_image_count = 3
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-purging-several-user-policys-answers-for-the-one-still-held"></a>

#### [purging-several-user-policys-answers-for-the-one-still-held](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_purging.py): pass

when the superadmin deletes a still assigned user policy and an unused one at once, the unused one comes back in the processed list and the assigned one comes back in the failed list because it is still referenced

Given

- 1 unused policies of the user policy kind and one superadmin, with the user policy assigned to that user also among the targets
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy target-1: up to 10 folders per user

When

- ResourcePolicyAdapter.partial_bulk_purge_user_resource_policies: user-1 deletes 2 policies of the user policy kind at once

Then

- the unused user policy comes back in the processed list and the one still assigned comes back in the failed list because it is still referenced
  - successes count = 1
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 10
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - failed count = 1
  - failed[0].id: same as the id of the policy assigned to the caller
  - failed[0].message: a reason containing 'Foreign key'

### partial_bulk_update_keypair_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-keypair-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-keypair-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

a user granted nothing trying to edit several policies of the keypair policy kind at once gets none edited and every one in the failed list for not enough permission

Given

- 2 unused policies of the keypair policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy target-1: up to 5 concurrent sessions
  - Keypair policy target-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.partial_bulk_update_keypair_resource_policies: user-1 updates 2 policies of the keypair policy kind at once (the concurrent session count changed to 7)

Then

- no keypair policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-keypair-policys-at-once"></a>

#### [the-superadmin-edits-several-keypair-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

when the superadmin changes one limit of several policies of the keypair policy kind at once, they all come back with only that limit at the new value and nothing failed

Given

- 2 unused policies of the keypair policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy target-1: up to 5 concurrent sessions
  - Keypair policy target-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.partial_bulk_update_keypair_resource_policies: user-1 updates 2 policies of the keypair policy kind at once (the concurrent session count changed to 7)

Then

- every target keypair policy comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[0].total_resource_slots = []
  - successes[0].max_session_lifetime = 0
  - successes[0].max_concurrent_sessions = 7
  - successes[0].max_pending_session_count = None
  - successes[0].max_priority = None
  - successes[0].max_pending_session_resource_slots = None
  - successes[0].max_concurrent_sftp_sessions = 1
  - successes[0].max_containers_per_session = 1
  - successes[0].idle_timeout = 3600
  - successes[0].allowed_vfolder_hosts = []
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - successes[1].total_resource_slots = []
  - successes[1].max_session_lifetime = 0
  - successes[1].max_concurrent_sessions = 7
  - successes[1].max_pending_session_count = None
  - successes[1].max_priority = None
  - successes[1].max_pending_session_resource_slots = None
  - successes[1].max_concurrent_sftp_sessions = 1
  - successes[1].max_containers_per_session = 1
  - successes[1].idle_timeout = 3600
  - successes[1].allowed_vfolder_hosts = []
  - failed = []

### partial_bulk_update_project_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-project-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-project-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

a user granted nothing trying to edit several policies of the project policy kind at once gets none edited and every one in the failed list for not enough permission

Given

- 2 unused policies of the project policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy target-1: up to 10 folders per project
  - Project resource policy target-2: up to 10 folders per project

When

- ResourcePolicyAdapter.partial_bulk_update_project_resource_policies: user-1 updates 2 policies of the project policy kind at once (the vfolder count changed to 20)

Then

- no project policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-project-policys-at-once"></a>

#### [the-superadmin-edits-several-project-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

when the superadmin changes one limit of several policies of the project policy kind at once, they all come back with only that limit at the new value and nothing failed

Given

- 2 unused policies of the project policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy target-1: up to 10 folders per project
  - Project resource policy target-2: up to 10 folders per project

When

- ResourcePolicyAdapter.partial_bulk_update_project_resource_policies: user-1 updates 2 policies of the project policy kind at once (the vfolder count changed to 20)

Then

- every target project policy comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 20
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_network_count = 3
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].max_vfolder_count = 20
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_network_count = 3
  - failed = []

### partial_bulk_update_user_resource_policies

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-user-policys"></a>

#### [a-user-granted-nothing-edits-none-of-several-user-policys](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

a user granted nothing trying to edit several policies of the user policy kind at once gets none edited and every one in the failed list for not enough permission

Given

- 2 unused policies of the user policy kind and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy target-1: up to 10 folders per user
  - User resource policy target-2: up to 10 folders per user

When

- ResourcePolicyAdapter.partial_bulk_update_user_resource_policies: user-1 updates 2 policies of the user policy kind at once (the vfolder count changed to 20)

Then

- no user policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-user-policys-at-once"></a>

#### [the-superadmin-edits-several-user-policys-at-once](/tests/scenario/bai_scenario/manager/resource_policy/test_partial_bulk_editing.py): pass

when the superadmin changes one limit of several policies of the user policy kind at once, they all come back with only that limit at the new value and nothing failed

Given

- 2 unused policies of the user policy kind and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy target-1: up to 10 folders per user
  - User resource policy target-2: up to 10 folders per user

When

- ResourcePolicyAdapter.partial_bulk_update_user_resource_policies: user-1 updates 2 policies of the user policy kind at once (the vfolder count changed to 20)

Then

- every target user policy comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id = 'target-1'
  - successes[0].name = 'target-1'
  - successes[0].created_at: the time this run wrote
  - successes[0].max_vfolder_count = 20
  - successes[0].max_concurrent_logins = None
  - successes[0].max_quota_scope_size = ('-1', '-1')
  - successes[0].max_session_count_per_model_session = 10
  - successes[0].max_customized_image_count = 3
  - successes[1].id = 'target-2'
  - successes[1].name = 'target-2'
  - successes[1].created_at: the time this run wrote
  - successes[1].max_vfolder_count = 20
  - successes[1].max_concurrent_logins = None
  - successes[1].max_quota_scope_size = ('-1', '-1')
  - successes[1].max_session_count_per_model_session = 10
  - successes[1].max_customized_image_count = 3
  - failed = []

### purge_keypair_resource_policy

<a id="retiring-the-superadmin-purges-a-keypair-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-keypair-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin deletes an unused keypair policy, the deleted name comes back and searching right after finds nothing

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1 deletes keypair-policy-2 and searches again with the same name

Then

- the deleted name comes back and searching again finds nothing
  - name = 'keypair-policy-2'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the same keypair policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1 deletes keypair-policy-2 and searches again with the same name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="retiring-purging-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a name no keypair policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1 deletes nobody and searches again with the same name

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="retiring-purging-a-keypair-policy-still-held-is-refused"></a>

#### [purging-a-keypair-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a keypair policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec

Given

- one superadmin and the keypair policy still assigned to that user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.purge_keypair_resource_policy: user-1 deletes keypair-policy-1 and searches again with the same name

Then

- the call is rejected
  - rejected: ForeignKeyViolationError

### purge_project_resource_policy

<a id="retiring-the-superadmin-purges-a-project-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-project-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin deletes an unused project policy, the deleted name comes back and searching right after finds nothing

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1 deletes project-policy-1 and searches again with the same name

Then

- the deleted name comes back and searching again finds nothing
  - name = 'project-policy-1'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-project-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the same project policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1 deletes project-policy-1 and searches again with the same name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="retiring-purging-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a name no project policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1 deletes nobody and searches again with the same name

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="retiring-purging-a-project-policy-still-held-is-refused"></a>

#### [purging-a-project-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a project policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec

Given

- one superadmin and the project policy still assigned to that user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.purge_project_resource_policy: user-1 deletes default and searches again with the same name

Then

- the call is rejected
  - rejected: ForeignKeyViolationError

### purge_user_resource_policy

<a id="retiring-the-superadmin-purges-a-user-policy-nobody-holds"></a>

#### [the-superadmin-purges-a-user-policy-nobody-holds](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin deletes an unused user policy, the deleted name comes back and searching right after finds nothing

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1 deletes user-policy-2 and searches again with the same name

Then

- the deleted name comes back and searching again finds nothing
  - name = 'user-policy-2'
  - found afterwards = 0

<a id="retiring-a-user-granted-nothing-may-not-purge-a-user-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the same user policy exists and a user granted nothing tries to delete it, the call is rejected before the delete logic because the policy cannot be found

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1 deletes user-policy-2 and searches again with the same name

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="retiring-purging-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [purging-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a name no user policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1 deletes nobody and searches again with the same name

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="retiring-purging-a-user-policy-still-held-is-refused"></a>

#### [purging-a-user-policy-still-held-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_retiring.py): pass

when the superadmin tries to delete a user policy still assigned to someone, the call is rejected because it is still referenced. the foreign key blocks it, not the purge spec

Given

- one superadmin and the user policy still assigned to that user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourcePolicyAdapter.purge_user_resource_policy: user-1 deletes user-policy-1 and searches again with the same name

Then

- the call is rejected
  - rejected: ForeignKeyViolationError

### update_keypair_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-keypair-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin clears a non-nullable entry of a keypair policy, the request is ignored and the node comes back with nothing changed

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (the concurrent session count cleared)

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-clearing-a-nullable-value-of-a-keypair-policy-empties-it"></a>

#### [clearing-a-nullable-value-of-a-keypair-policy-empties-it](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin clears the nullable entry of a keypair policy that holds a value, the node comes back with that entry empty

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions, up to 2 of them pending

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (the pending session count cleared)

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-giving-no-value-changes-nothing-of-a-keypair-policy"></a>

#### [giving-no-value-changes-nothing-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin names a keypair policy and gives no value, the node comes back with nothing changed

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (an empty request)

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 5
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-the-superadmin-changes-one-limit-of-a-keypair-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

one keypair policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (the concurrent session count changed to 7)

Then

- the whole keypair policy seeded in advance comes back
  - id = 'keypair-policy-2'
  - name = 'keypair-policy-2'
  - created_at: the time this run wrote
  - default_for_unspecified = <DefaultForUnspecified.UNLIMITED: 'UNLIMITED'>
  - total_resource_slots = []
  - max_session_lifetime = 0
  - max_concurrent_sessions = 7
  - max_pending_session_count = None
  - max_priority = None
  - max_pending_session_resource_slots = None
  - max_concurrent_sftp_sessions = 1
  - max_containers_per_session = 1
  - idle_timeout = 3600
  - allowed_vfolder_hosts = []

<a id="editing-a-user-granted-nothing-may-not-edit-a-keypair-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-keypair-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the same keypair policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found

Given

- one unused keypair policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (the concurrent session count changed to 7)

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="editing-editing-a-keypair-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-keypair-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin tries to edit a name no keypair policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates nobody (the concurrent session count changed to 7)

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="editing-moving-the-priority-cap-outside-the-session-range-is-refused"></a>

#### [moving-the-priority-cap-outside-the-session-range-is-refused](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin tries to move the priority cap of a keypair policy outside the session priority range, the call is rejected on a constraint violation

Given

- one unused keypair policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions

When

- ResourcePolicyAdapter.update_keypair_resource_policy: user-1 updates keypair-policy-2 (the priority cap changed to a value outside the session priority range)

Then

- the call is rejected
  - rejected: CheckConstraintViolationError

### update_project_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-project-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin clears a non-nullable entry of a project policy, the request is ignored and the node comes back with nothing changed

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1 updates project-policy-1 (the vfolder count cleared)

Then

- the whole project policy seeded in advance comes back
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-giving-no-value-changes-nothing-of-a-project-policy"></a>

#### [giving-no-value-changes-nothing-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin names a project policy and gives no value, the node comes back with nothing changed

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1 updates project-policy-1 (an empty request)

Then

- the whole project policy seeded in advance comes back
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-the-superadmin-changes-one-limit-of-a-project-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

one project policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1 updates project-policy-1 (the vfolder count changed to 20)

Then

- the whole project policy seeded in advance comes back
  - id = 'project-policy-1'
  - name = 'project-policy-1'
  - created_at: the time this run wrote
  - max_vfolder_count = 20
  - max_quota_scope_size = ('-1', '-1')
  - max_network_count = 3

<a id="editing-a-user-granted-nothing-may-not-edit-a-project-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-project-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the same project policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found

Given

- one unused project policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1 updates project-policy-1 (the vfolder count changed to 20)

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="editing-editing-a-project-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-project-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin tries to edit a name no project policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused project policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Project resource policy project-policy-1: up to 10 folders per project

When

- ResourcePolicyAdapter.update_project_resource_policy: user-1 updates nobody (the vfolder count changed to 20)

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update_user_resource_policy

<a id="editing-clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was"></a>

#### [clearing-a-non-nullable-value-of-a-user-policy-leaves-it-as-it-was](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin clears a non-nullable entry of a user policy, the request is ignored and the node comes back with nothing changed

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates user-policy-2 (the vfolder count cleared)

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-clearing-a-nullable-value-of-a-user-policy-empties-it"></a>

#### [clearing-a-nullable-value-of-a-user-policy-empties-it](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin clears the nullable entry of a user policy that holds a value, the node comes back with that entry empty

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user, up to 3 concurrent logins

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates user-policy-2 (the concurrent login count cleared)

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-giving-no-value-changes-nothing-of-a-user-policy"></a>

#### [giving-no-value-changes-nothing-of-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin names a user policy and gives no value, the node comes back with nothing changed

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates user-policy-2 (an empty request)

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 10
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-the-superadmin-changes-one-limit-of-a-user-policy"></a>

#### [the-superadmin-changes-one-limit-of-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

one user policy exists and the superadmin changes one limit, so only that limit takes the new value and the rest stays as it was

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates user-policy-2 (the vfolder count changed to 20)

Then

- the whole user policy seeded in advance comes back
  - id = 'user-policy-2'
  - name = 'user-policy-2'
  - created_at: the time this run wrote
  - max_vfolder_count = 20
  - max_concurrent_logins = None
  - max_quota_scope_size = ('-1', '-1')
  - max_session_count_per_model_session = 10
  - max_customized_image_count = 3

<a id="editing-a-user-granted-nothing-may-not-edit-a-user-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-user-policy](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the same user policy exists and a user granted nothing tries to edit it, the call is rejected before the edit logic because the policy cannot be found

Given

- one unused user policy and one user
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates user-policy-2 (the vfolder count changed to 20)

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="editing-editing-a-user-policy-name-nothing-answers-to-is-not-found"></a>

#### [editing-a-user-policy-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_policy/test_editing.py): pass

when the superadmin tries to edit a name no user policy holds, the call is rejected as no such target, not on a permission problem

Given

- one unused user policy and one superadmin
  - Domain home-1
  - Prepare one user with policies assigned
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - User resource policy user-policy-2: up to 10 folders per user

When

- ResourcePolicyAdapter.update_user_resource_policy: user-1 updates nobody (the vfolder count changed to 20)

Then

- the call is rejected
  - rejected: EntityNotFoundError

