## notification

[background](/src/ai/backend/manager/api/adapters/notification/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/notification/adapter.py)

Scenario: incomplete 6 / 18

- built from ops (16)
  - batch_load_channels_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - batch_load_rules_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - create_channel: representative success ✓ · representative rejection ✓
  - create_rule: representative success ✓ · representative rejection ✓
  - get_channel: representative success ✓ · representative rejection ✓
  - get_rule: representative success ✓ · representative rejection ✓
  - partial_bulk_purge_channels: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge_rules: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update_channels: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update_rules: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge_channel: representative success ✓ · representative rejection ✓
  - purge_rule: representative success ✓ · representative rejection ✓
  - search_channels: representative success ✓ · representative rejection ✓
  - search_rules: representative success ✓ · representative rejection ✓
  - update_channel: representative success ✓ · representative rejection ✓
  - update_rule: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - validate_channel: success present 1 · rejection present 2 (single_entity)
  - validate_rule: success present 1 · rejection present 3 (single_entity)

**batch_load_channels_by_ids**

| scenario | verdict |
|---|---|
| [a batch load with an empty id list brings an empty response without calling the lower layer](#reading_channels-a-batch-load-of-no-channel-ids-answers-an-empty-list) | answered |
| [when a user granted nothing batch-loads two channels, the call is not rejected and each item carries a rejection for not enough permission](#reading_channels-a-user-granted-nothing-batch-loading-channels-is-refused-per-item) | answered |
| [when the superadmin batch-loads two channels created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty](#reading_channels-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |

**batch_load_rules_by_ids**

| scenario | verdict |
|---|---|
| [a batch load with an empty id list brings an empty response without calling the lower layer](#reading_rules-a-batch-load-of-no-rule-ids-answers-an-empty-list) | answered |
| [when a user granted nothing batch-loads two rules, the call is not rejected and each item carries a rejection for not enough permission](#reading_rules-a-user-granted-nothing-batch-loading-rules-is-refused-per-item) | answered |
| [when the superadmin batch-loads two rules created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty](#reading_rules-the-superadmin-batch-load-leaves-a-missing-rule-id-empty) | answered |

**create_channel**

| scenario | verdict |
|---|---|
| [when the superadmin creates a channel marked disabled, a disabled channel comes back](#creating_channels-a-channel-made-disabled-answers-disabled) | answered |
| [when the superadmin creates a webhook channel with only a name and a URL, the whole channel comes back active with an empty description](#creating_channels-the-superadmin-makes-a-webhook-channel) | answered |
| [when the superadmin creates an email channel with the SMTP connection, the sender, the recipients and the auth credentials, the whole channel comes back with the auth username and without the password](#creating_channels-the-superadmin-makes-an-email-channel) | answered |
| [when a channel is created as the email type with a webhook spec, reading the written row back rejects it because the spec does not match the type, and the write is rolled back](#creating_channels-a-channel-type-and-a-spec-that-disagree-are-refused) | rejected |
| [creating a channel with a spec naming neither webhook nor email is rejected as invalid input](#creating_channels-a-spec-naming-neither-webhook-nor-email-is-refused) | rejected |
| [when a user who is not the superadmin creates a channel, it is rejected for an insufficient role](#creating_channels-a-user-who-is-not-the-superadmin-may-not-make-a-channel) | rejected |
| [when the monitor creates a channel, it is rejected for an insufficient role. The monitor passes reads only](#creating_channels-the-monitor-may-not-make-a-channel) | rejected |

**create_rule**

| scenario | verdict |
|---|---|
| [when the superadmin creates a rule marked disabled, a disabled rule comes back](#creating_rules-a-rule-made-disabled-answers-disabled) | answered |
| [a rule created against a channel id no row answers to is created anyway. There is no foreign key between the two tables](#creating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same) | answered |
| [when the superadmin creates a rule with a type, a channel and a template, the whole rule comes back active with an empty description](#creating_rules-the-superadmin-makes-a-rule-through-a-channel) | answered |
| [when a user who is not the superadmin creates a rule, it is rejected for an insufficient role](#creating_rules-a-user-who-is-not-the-superadmin-may-not-make-a-rule) | rejected |
| [when the monitor creates a rule, it is rejected for an insufficient role. The monitor passes reads only](#creating_rules-the-monitor-may-not-make-a-rule) | rejected |

**get_channel**

| scenario | verdict |
|---|---|
| [with one channel, when the superadmin gets it by id, the whole channel comes back](#reading_channels-the-superadmin-reads-a-channel-by-id) | answered |
| [when a user granted nothing gets a channel by id, it is rejected for not enough permission, even when the channel records that user as its creator](#reading_channels-a-user-granted-nothing-may-not-read-a-channel) | rejected |
| [when a user granted nothing gets an unknown id, it is rejected for not enough permission rather than for a missing target, because the permission check runs first and a missing row holds no grant either](#reading_channels-a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission) | rejected |
| [when the monitor gets a channel by id, it is rejected for not enough permission. Search passes, but a get by id is a permission check and the monitor holds no permission for it either](#reading_channels-the-monitor-may-not-read-a-channel-by-id) | rejected |
| [when the superadmin gets an id nothing answers to, it is rejected because no target is found](#reading_channels-the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found) | rejected |

**get_rule**

| scenario | verdict |
|---|---|
| [with one rule, when the superadmin gets it by id, the whole rule comes back](#reading_rules-the-superadmin-reads-a-rule-by-id) | answered |
| [when a user granted nothing gets a rule by id, it is rejected for not enough permission](#reading_rules-a-user-granted-nothing-may-not-read-a-rule) | rejected |
| [when the superadmin gets an id nothing answers to, it is rejected because no target is found](#reading_rules-the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found) | rejected |

**partial_bulk_purge_channels**

| scenario | verdict |
|---|---|
| [when a user granted nothing purges several channels at once, nothing is purged and every one comes back in the failed list because permission is not enough](#partial_bulk_purging_channels-a-user-granted-nothing-purges-none-of-several-channels) | answered |
| [when the superadmin purges two channels and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging_channels-purging-several-channels-answers-for-the-missing-one) | answered |

**partial_bulk_purge_rules**

| scenario | verdict |
|---|---|
| [when a user granted nothing purges several rules at once, nothing is purged and every one comes back in the failed list because permission is not enough](#partial_bulk_purging_rules-a-user-granted-nothing-purges-none-of-several-rules) | answered |
| [when the superadmin purges two rules and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging_rules-purging-several-rules-answers-for-the-missing-one) | answered |

**partial_bulk_update_channels**

| scenario | verdict |
|---|---|
| [when a user granted nothing edits several channels at once, nothing is edited and every one comes back in the failed list because permission is not enough](#partial_bulk_editing_channels-a-user-granted-nothing-edits-none-of-several-channels) | answered |
| [when the superadmin changes the description of two channels at once, both come back with the new description and nothing failed](#partial_bulk_editing_channels-the-superadmin-describes-several-channels-at-once) | answered |

**partial_bulk_update_rules**

| scenario | verdict |
|---|---|
| [when a user granted nothing edits several rules at once, nothing is edited and every one comes back in the failed list because permission is not enough](#partial_bulk_editing_rules-a-user-granted-nothing-edits-none-of-several-rules) | answered |
| [when the superadmin changes the description of two rules at once, both come back with the new description and nothing failed](#partial_bulk_editing_rules-the-superadmin-describes-several-rules-at-once) | answered |

**purge_channel**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a channel a rule points at, it is deleted all the same and the id of the deleted channel comes back. There is no foreign key between the two tables, so the rule stays](#retiring_channels-a-channel-a-rule-points-at-is-deleted-all-the-same) | answered |
| [with one channel, when the superadmin deletes it, the id of the deleted channel comes back](#retiring_channels-the-superadmin-deletes-a-channel) | answered |
| [when a user granted nothing deletes a channel, it is rejected for not enough permission](#retiring_channels-a-user-granted-nothing-may-not-delete-a-channel) | rejected |
| [when the superadmin deletes an id nothing answers to, it is rejected because no target is found](#retiring_channels-the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found) | rejected |

**purge_rule**

| scenario | verdict |
|---|---|
| [with one rule, when the superadmin deletes it, the id of the deleted rule comes back](#retiring_rules-the-superadmin-deletes-a-rule) | answered |
| [when a user granted nothing deletes a rule, it is rejected for not enough permission](#retiring_rules-a-user-granted-nothing-may-not-delete-a-rule) | rejected |
| [when the superadmin deletes an id nothing answers to, it is rejected because no target is found](#retiring_rules-the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found) | rejected |

**search_channels**

| scenario | verdict |
|---|---|
| [with a webhook channel and an email channel, a get filtered by the email type brings back only the email channel](#searching_channels-a-channel-type-filter-narrows-the-answer-to-that-kind) | answered |
| [a get filtered by the name of one of two channels brings back only that channel](#searching_channels-a-name-filter-narrows-the-answer-to-that-channel) | answered |
| [with active and inactive channels mixed, a get filtered by enabled brings back only the active ones](#searching_channels-an-enabled-filter-leaves-only-the-enabled-channels) | answered |
| [with two channels, asking for only the first item brings one item back and the response says there is a next page](#searching_channels-asking-for-the-first-channel-only-says-there-is-a-next-page) | answered |
| [when the monitor gets without a filter, it receives the same response as the superadmin](#searching_channels-the-monitor-searches-channels-like-the-superadmin) | answered |
| [with two channels, a get without a filter brings both of them back](#searching_channels-the-superadmin-counts-every-channel-laid) | answered |
| [when a user who is not the superadmin gets without a filter, it is rejected for an insufficient role](#searching_channels-a-user-who-is-not-the-superadmin-may-not-search-channels) | rejected |

**search_rules**

| scenario | verdict |
|---|---|
| [a get filtered by the name of one of two rules brings back only that rule](#searching_rules-a-name-filter-narrows-the-answer-to-that-rule) | answered |
| [a get filtered by the type of one of two rules with different types brings back only that rule](#searching_rules-a-rule-type-filter-narrows-the-answer-to-that-kind) | answered |
| [with active and inactive rules mixed, a get filtered by enabled brings back only the active ones](#searching_rules-an-enabled-filter-leaves-only-the-enabled-rules) | answered |
| [when the monitor gets without a filter, it receives the same response as the superadmin](#searching_rules-the-monitor-searches-rules-like-the-superadmin) | answered |
| [with two rules, a get without a filter brings both of them back](#searching_rules-the-superadmin-counts-every-rule-laid) | answered |
| [when a user who is not the superadmin gets without a filter, it is rejected for an insufficient role](#searching_rules-a-user-who-is-not-the-superadmin-may-not-search-rules) | rejected |

**update_channel**

| scenario | verdict |
|---|---|
| [editing without naming any field brings the channel back unchanged](#editing_channels-an-edit-naming-no-field-changes-nothing) | answered |
| [when the spec of a webhook channel moves to another URL, the channel comes back with the new URL](#editing_channels-changing-a-webhook-spec-moves-the-channel-to-the-new-url) | answered |
| [when the description of a channel that has one is cleared, the channel comes back with an empty description](#editing_channels-clearing-a-channel-description-leaves-it-empty) | answered |
| [when an active channel is changed to disabled, a disabled channel comes back](#editing_channels-disabling-a-channel-answers-it-disabled) | answered |
| [when the superadmin changes only the name, the whole channel comes back with the new name and everything else unchanged](#editing_channels-the-superadmin-renaming-a-channel-leaves-the-rest) | answered |
| [when a user granted nothing changes the name, it is rejected for not enough permission](#editing_channels-a-user-granted-nothing-may-not-edit-a-channel) | rejected |
| [editing a channel with a spec naming neither webhook nor email is rejected as invalid input](#editing_channels-an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused) | rejected |
| [when the superadmin edits an id nothing answers to, it is rejected because no target is found](#editing_channels-the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found) | rejected |

**update_rule**

| scenario | verdict |
|---|---|
| [editing without naming any field brings the rule back unchanged](#editing_rules-a-rule-edit-naming-no-field-changes-nothing) | answered |
| [when the template of a rule changes, the rule comes back with the new template](#editing_rules-changing-a-rule-template-answers-the-new-template) | answered |
| [when the description of a rule that has one is cleared, the rule comes back with an empty description](#editing_rules-clearing-a-rule-description-leaves-it-empty) | answered |
| [when an active rule is changed to disabled, a disabled rule comes back](#editing_rules-disabling-a-rule-answers-it-disabled) | answered |
| [when the superadmin changes only the name, the whole rule comes back with the new name and everything else unchanged](#editing_rules-the-superadmin-renaming-a-rule-leaves-the-rest) | answered |
| [when a user granted nothing changes the name, it is rejected for not enough permission](#editing_rules-a-user-granted-nothing-may-not-edit-a-rule) | rejected |
| [when the superadmin edits an id nothing answers to, it is rejected because no target is found](#editing_rules-the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found) | rejected |

**validate_channel**

| scenario | verdict |
|---|---|
| [with one webhook channel, when the superadmin validates it with a test message, the id of the validated channel comes back](#validating_channels-the-superadmin-validates-a-webhook-channel) | answered |
| [when a user granted nothing validates a channel, it is rejected for not enough permission](#validating_channels-a-user-granted-nothing-may-not-validate-a-channel) | rejected |
| [when the superadmin validates an id nothing answers to, it is rejected because no target is found](#validating_channels-the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found) | rejected |

**validate_rule**

| scenario | verdict |
|---|---|
| [with one session-started rule, when the superadmin validates it with test data of that type, the string made by putting the data into the template comes back](#validating_rules-the-superadmin-validates-a-rule-with-test-data) | answered |
| [validating a rule pointing at an unknown channel id is rejected because no channel is found](#validating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused) | rejected |
| [when a user granted nothing validates a rule, it is rejected for not enough permission](#validating_rules-a-user-granted-nothing-may-not-validate-a-rule) | rejected |
| [when the superadmin validates an id nothing answers to, it is rejected because no target is found](#validating_rules-the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_channels_by_ids

<a id="reading_channels-a-batch-load-of-no-channel-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-channel-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

a batch load with an empty id list brings an empty response without calling the lower layer

Given

- two webhook channels and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.batch_load_channels_by_ids: user-1 batch-loads with an empty id list

Then

- an empty response comes back
  - items = []

<a id="reading_channels-a-user-granted-nothing-batch-loading-channels-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-channels-is-refused-per-item](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when a user granted nothing batch-loads two channels, the call is not rejected and each item carries a rejection for not enough permission

Given

- two webhook channels and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.batch_load_channels_by_ids: user-1 batch-loads the 2 channels created in advance

Then

- each item carries a rejection for not enough permission
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

<a id="reading_channels-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when the superadmin batch-loads two channels created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.batch_load_channels_by_ids: user-1 batch-loads the 2 channels created in advance and one unknown id

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].name = 'wanted-1'
  - items[0].description = None
  - items[0].channel_type = 'webhook'
  - items[0].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - items[0].spec.url = 'https://hooks.example.test/notify'
  - items[0].enabled = True
  - items[0].created_by: same as the user who created it
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].name = 'other-1'
  - items[1].description = None
  - items[1].channel_type = 'webhook'
  - items[1].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - items[1].spec.url = 'https://hooks.example.test/notify'
  - items[1].enabled = True
  - items[1].created_by: same as the user who created it
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[2] = None

### batch_load_rules_by_ids

<a id="reading_rules-a-batch-load-of-no-rule-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-rule-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

a batch load with an empty id list brings an empty response without calling the lower layer

Given

- two rules pointing at the same webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.batch_load_rules_by_ids: user-1 batch-loads with an empty id list

Then

- an empty response comes back
  - items = []

<a id="reading_rules-a-user-granted-nothing-batch-loading-rules-is-refused-per-item"></a>

#### [a-user-granted-nothing-batch-loading-rules-is-refused-per-item](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

when a user granted nothing batch-loads two rules, the call is not rejected and each item carries a rejection for not enough permission

Given

- two rules pointing at the same webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.batch_load_rules_by_ids: user-1 batch-loads the 2 rules created in advance

Then

- each item carries a rejection for not enough permission
  - len(items) = 2
  - items[0] = 'NotEnoughPermission'
  - items[1] = 'NotEnoughPermission'

<a id="reading_rules-the-superadmin-batch-load-leaves-a-missing-rule-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-rule-id-empty](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

when the superadmin batch-loads two rules created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.batch_load_rules_by_ids: user-1 batch-loads the 2 rules created in advance and one unknown id

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0].id: skipped: the database generates it
  - items[0].name = 'wanted-1'
  - items[0].description = None
  - items[0].rule_type = 'session.started'
  - items[0].channel_id: same as the channel it points at
  - items[0].message_template = 'Session {{ session_name }} is {{ status }}'
  - items[0].enabled = True
  - items[0].created_by: same as the user who created it
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].name = 'other-1'
  - items[1].description = None
  - items[1].rule_type = 'session.started'
  - items[1].channel_id: same as the channel it points at
  - items[1].message_template = 'Session {{ session_name }} is {{ status }}'
  - items[1].enabled = True
  - items[1].created_by: same as the user who created it
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[2] = None

### create_channel

<a id="creating_channels-a-channel-made-disabled-answers-disabled"></a>

#### [a-channel-made-disabled-answers-disabled](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when the superadmin creates a channel marked disabled, a disabled channel comes back

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the webhook channel muted

Then

- the whole channel just created comes back
  - id: skipped: the database generates it
  - name = 'muted'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = False
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_channels-the-superadmin-makes-a-webhook-channel"></a>

#### [the-superadmin-makes-a-webhook-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when the superadmin creates a webhook channel with only a name and a URL, the whole channel comes back active with an empty description

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the webhook channel alerts

Then

- the whole channel just created comes back
  - id: skipped: the database generates it
  - name = 'alerts'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_channels-the-superadmin-makes-an-email-channel"></a>

#### [the-superadmin-makes-an-email-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when the superadmin creates an email channel with the SMTP connection, the sender, the recipients and the auth credentials, the whole channel comes back with the auth username and without the password

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the email channel mail

Then

- the whole channel just created comes back
  - id: skipped: the database generates it
  - name = 'mail'
  - description = None
  - channel_type = 'email'
  - spec.channel_type = <NotificationChannelTypeDTO.EMAIL: 'email'>
  - spec.smtp.host = 'smtp.example.test'
  - spec.smtp.port = 587
  - spec.smtp.use_tls = True
  - spec.smtp.timeout = 30
  - spec.message.from_email = 'noreply@example.test'
  - spec.message.to_emails = ['ops@example.test']
  - spec.message.subject_template = None
  - spec.auth.username = 'mailer'
  - spec.auth.password: skipped: the response type has no such place
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_channels-a-channel-type-and-a-spec-that-disagree-are-refused"></a>

#### [a-channel-type-and-a-spec-that-disagree-are-refused](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when a channel is created as the email type with a webhook spec, reading the written row back rejects it because the spec does not match the type, and the write is rolled back

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the email channel mismatched

Then

- the call is rejected
  - rejected: BackendAISchemaValidationFailed

<a id="creating_channels-a-spec-naming-neither-webhook-nor-email-is-refused"></a>

#### [a-spec-naming-neither-webhook-nor-email-is-refused](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

creating a channel with a spec naming neither webhook nor email is rejected as invalid input

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the webhook channel empty

Then

- the call is rejected
  - rejected: InvalidNotificationSpec

<a id="creating_channels-a-user-who-is-not-the-superadmin-may-not-make-a-channel"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when a user who is not the superadmin creates a channel, it is rejected for an insufficient role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the webhook channel by-a-user

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating_channels-the-monitor-may-not-make-a-channel"></a>

#### [the-monitor-may-not-make-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_channels.py): pass

when the monitor creates a channel, it is rejected for an insufficient role. The monitor passes reads only

Given

- one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- NotificationAdapter.create_channel: user-1 creates the webhook channel by-the-monitor

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### create_rule

<a id="creating_rules-a-rule-made-disabled-answers-disabled"></a>

#### [a-rule-made-disabled-answers-disabled](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py): pass

when the superadmin creates a rule marked disabled, a disabled rule comes back

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.create_rule: user-1 creates the rule muted pointing at the channel channel-1

Then

- the whole rule just created comes back
  - id: skipped: the database generates it
  - name = 'muted'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = False
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same"></a>

#### [a-rule-pointing-at-a-channel-id-nothing-answers-to-is-made-all-the-same](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py): pass

a rule created against a channel id no row answers to is created anyway. There is no foreign key between the two tables

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.create_rule: user-1 creates the rule orphan pointing at an unknown channel id

Then

- the whole rule just created comes back
  - id: skipped: the database generates it
  - name = 'orphan'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_rules-the-superadmin-makes-a-rule-through-a-channel"></a>

#### [the-superadmin-makes-a-rule-through-a-channel](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py): pass

when the superadmin creates a rule with a type, a channel and a template, the whole rule comes back active with an empty description

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.create_rule: user-1 creates the rule on-start pointing at the channel channel-1

Then

- the whole rule just created comes back
  - id: skipped: the database generates it
  - name = 'on-start'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating_rules-a-user-who-is-not-the-superadmin-may-not-make-a-rule"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-a-rule](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py): pass

when a user who is not the superadmin creates a rule, it is rejected for an insufficient role

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.create_rule: user-1 creates the rule by-a-user pointing at the channel channel-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating_rules-the-monitor-may-not-make-a-rule"></a>

#### [the-monitor-may-not-make-a-rule](/tests/scenario/bai_scenario/manager/notification/test_creating_rules.py): pass

when the monitor creates a rule, it is rejected for an insufficient role. The monitor passes reads only

Given

- one webhook channel and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.create_rule: user-1 creates the rule by-the-monitor pointing at the channel channel-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get_channel

<a id="reading_channels-the-superadmin-reads-a-channel-by-id"></a>

#### [the-superadmin-reads-a-channel-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

with one channel, when the superadmin gets it by id, the whole channel comes back

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.get_channel: user-1 gets the channel channel-1

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading_channels-a-user-granted-nothing-may-not-read-a-channel"></a>

#### [a-user-granted-nothing-may-not-read-a-channel](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when a user granted nothing gets a channel by id, it is rejected for not enough permission, even when the channel records that user as its creator

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.get_channel: user-1 gets the channel channel-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_channels-a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-reading-an-unknown-channel-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when a user granted nothing gets an unknown id, it is rejected for not enough permission rather than for a missing target, because the permission check runs first and a missing row holds no grant either

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.get_channel: user-1 gets an unknown id

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_channels-the-monitor-may-not-read-a-channel-by-id"></a>

#### [the-monitor-may-not-read-a-channel-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when the monitor gets a channel by id, it is rejected for not enough permission. Search passes, but a get by id is a permission check and the monitor holds no permission for it either

Given

- one webhook channel and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.get_channel: user-1 gets the channel channel-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_channels-the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_reading_channels.py): pass

when the superadmin gets an id nothing answers to, it is rejected because no target is found

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.get_channel: user-1 gets an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get_rule

<a id="reading_rules-the-superadmin-reads-a-rule-by-id"></a>

#### [the-superadmin-reads-a-rule-by-id](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

with one rule, when the superadmin gets it by id, the whole rule comes back

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.get_rule: user-1 gets the rule rule-1

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading_rules-a-user-granted-nothing-may-not-read-a-rule"></a>

#### [a-user-granted-nothing-may-not-read-a-rule](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

when a user granted nothing gets a rule by id, it is rejected for not enough permission

Given

- one rule and the webhook channel it points at, and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.get_rule: user-1 gets the rule rule-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_rules-the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_reading_rules.py): pass

when the superadmin gets an id nothing answers to, it is rejected because no target is found

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.get_rule: user-1 gets an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_purge_channels

<a id="partial_bulk_purging_channels-a-user-granted-nothing-purges-none-of-several-channels"></a>

#### [a-user-granted-nothing-purges-none-of-several-channels](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_purging_channels.py): pass

when a user granted nothing purges several channels at once, nothing is purged and every one comes back in the failed list because permission is not enough

Given

- two webhook channels and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.partial_bulk_purge_channels: user-1 purges 2 channels at once

Then

- nothing is processed and everything created in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the thing created in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the thing created in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging_channels-purging-several-channels-answers-for-the-missing-one"></a>

#### [purging-several-channels-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_purging_channels.py): pass

when the superadmin purges two channels and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.partial_bulk_purge_channels: user-1 purges 2 channels and one unknown id at once

Then

- every channel created in advance comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = None
  - successes[0].channel_type = 'webhook'
  - successes[0].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - successes[0].spec.url = 'https://hooks.example.test/notify'
  - successes[0].enabled = True
  - successes[0].created_by: same as the user who created it
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = None
  - successes[1].channel_type = 'webhook'
  - successes[1].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - successes[1].spec.url = 'https://hooks.example.test/notify'
  - successes[1].enabled = True
  - successes[1].created_by: same as the user who created it
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_purge_rules

<a id="partial_bulk_purging_rules-a-user-granted-nothing-purges-none-of-several-rules"></a>

#### [a-user-granted-nothing-purges-none-of-several-rules](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_purging_rules.py): pass

when a user granted nothing purges several rules at once, nothing is purged and every one comes back in the failed list because permission is not enough

Given

- two rules pointing at the same webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.partial_bulk_purge_rules: user-1 purges 2 rules at once

Then

- nothing is processed and everything created in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the thing created in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the thing created in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging_rules-purging-several-rules-answers-for-the-missing-one"></a>

#### [purging-several-rules-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_purging_rules.py): pass

when the superadmin purges two rules and one unknown id at once, the two come back as they were before the purge and the unknown id comes back in the failed list because no target answers to it

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.partial_bulk_purge_rules: user-1 purges 2 rules and one unknown id at once

Then

- every rule created in advance comes back in the processed list and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = None
  - successes[0].rule_type = 'session.started'
  - successes[0].channel_id: same as the channel it points at
  - successes[0].message_template = 'Session {{ session_name }} is {{ status }}'
  - successes[0].enabled = True
  - successes[0].created_by: same as the user who created it
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = None
  - successes[1].rule_type = 'session.started'
  - successes[1].channel_id: same as the channel it points at
  - successes[1].message_template = 'Session {{ session_name }} is {{ status }}'
  - successes[1].enabled = True
  - successes[1].created_by: same as the user who created it
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update_channels

<a id="partial_bulk_editing_channels-a-user-granted-nothing-edits-none-of-several-channels"></a>

#### [a-user-granted-nothing-edits-none-of-several-channels](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_editing_channels.py): pass

when a user granted nothing edits several channels at once, nothing is edited and every one comes back in the failed list because permission is not enough

Given

- two webhook channels and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.partial_bulk_update_channels: user-1 edits the description of 2 channels at once

Then

- nothing is processed and everything created in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the thing created in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the thing created in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing_channels-the-superadmin-describes-several-channels-at-once"></a>

#### [the-superadmin-describes-several-channels-at-once](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_editing_channels.py): pass

when the superadmin changes the description of two channels at once, both come back with the new description and nothing failed

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.partial_bulk_update_channels: user-1 edits the description of 2 channels at once

Then

- every channel created in advance comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'the description changed all at once'
  - successes[0].channel_type = 'webhook'
  - successes[0].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - successes[0].spec.url = 'https://hooks.example.test/notify'
  - successes[0].enabled = True
  - successes[0].created_by: same as the user who created it
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = 'the description changed all at once'
  - successes[1].channel_type = 'webhook'
  - successes[1].spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - successes[1].spec.url = 'https://hooks.example.test/notify'
  - successes[1].enabled = True
  - successes[1].created_by: same as the user who created it
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### partial_bulk_update_rules

<a id="partial_bulk_editing_rules-a-user-granted-nothing-edits-none-of-several-rules"></a>

#### [a-user-granted-nothing-edits-none-of-several-rules](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_editing_rules.py): pass

when a user granted nothing edits several rules at once, nothing is edited and every one comes back in the failed list because permission is not enough

Given

- two rules pointing at the same webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.partial_bulk_update_rules: user-1 edits the description of 2 rules at once

Then

- nothing is processed and everything created in advance comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the thing created in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the thing created in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing_rules-the-superadmin-describes-several-rules-at-once"></a>

#### [the-superadmin-describes-several-rules-at-once](/tests/scenario/bai_scenario/manager/notification/test_partial_bulk_editing_rules.py): pass

when the superadmin changes the description of two rules at once, both come back with the new description and nothing failed

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.partial_bulk_update_rules: user-1 edits the description of 2 rules at once

Then

- every rule created in advance comes back in the processed list and nothing failed
  - successes count = 2
  - successes[0].id: skipped: the database generates it
  - successes[0].name = 'wanted-1'
  - successes[0].description = 'the description changed all at once'
  - successes[0].rule_type = 'session.started'
  - successes[0].channel_id: same as the channel it points at
  - successes[0].message_template = 'Session {{ session_name }} is {{ status }}'
  - successes[0].enabled = True
  - successes[0].created_by: same as the user who created it
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: skipped: the database generates it
  - successes[1].name = 'other-1'
  - successes[1].description = 'the description changed all at once'
  - successes[1].rule_type = 'session.started'
  - successes[1].channel_id: same as the channel it points at
  - successes[1].message_template = 'Session {{ session_name }} is {{ status }}'
  - successes[1].enabled = True
  - successes[1].created_by: same as the user who created it
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### purge_channel

<a id="retiring_channels-a-channel-a-rule-points-at-is-deleted-all-the-same"></a>

#### [a-channel-a-rule-points-at-is-deleted-all-the-same](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py): pass

when the superadmin deletes a channel a rule points at, it is deleted all the same and the id of the deleted channel comes back. There is no foreign key between the two tables, so the rule stays

Given

- one channel and one rule pointing at it, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.purge_channel: user-1 deletes the channel channel-1

Then

- the id of the deleted channel comes back
  - id: same as the channel created in advance

<a id="retiring_channels-the-superadmin-deletes-a-channel"></a>

#### [the-superadmin-deletes-a-channel](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py): pass

with one channel, when the superadmin deletes it, the id of the deleted channel comes back

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.purge_channel: user-1 deletes the channel channel-1

Then

- the id of the deleted channel comes back
  - id: same as the channel created in advance

<a id="retiring_channels-a-user-granted-nothing-may-not-delete-a-channel"></a>

#### [a-user-granted-nothing-may-not-delete-a-channel](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py): pass

when a user granted nothing deletes a channel, it is rejected for not enough permission

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.purge_channel: user-1 deletes the channel channel-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring_channels-the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-deleting-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_retiring_channels.py): pass

when the superadmin deletes an id nothing answers to, it is rejected because no target is found

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.purge_channel: user-1 deletes an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### purge_rule

<a id="retiring_rules-the-superadmin-deletes-a-rule"></a>

#### [the-superadmin-deletes-a-rule](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py): pass

with one rule, when the superadmin deletes it, the id of the deleted rule comes back

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.purge_rule: user-1 deletes the rule rule-1

Then

- the id of the deleted rule comes back
  - id: same as the rule created in advance

<a id="retiring_rules-a-user-granted-nothing-may-not-delete-a-rule"></a>

#### [a-user-granted-nothing-may-not-delete-a-rule](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py): pass

when a user granted nothing deletes a rule, it is rejected for not enough permission

Given

- one rule and the webhook channel it points at, and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.purge_rule: user-1 deletes the rule rule-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring_rules-the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-deleting-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_retiring_rules.py): pass

when the superadmin deletes an id nothing answers to, it is rejected because no target is found

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.purge_rule: user-1 deletes an unknown id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search_channels

<a id="searching_channels-a-channel-type-filter-narrows-the-answer-to-that-kind"></a>

#### [a-channel-type-filter-narrows-the-answer-to-that-kind](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

with a webhook channel and an email channel, a get filtered by the email type brings back only the email channel

Given

- one webhook channel and one email channel, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Email channel mail-channel-1: sends to ops@example.test through smtp.example.test

When

- NotificationAdapter.search_channels: user-1 gets channels filtered by the email type

Then

- only the one channel matching the filter comes back
  - items = ['mail-channel-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-a-name-filter-narrows-the-answer-to-that-channel"></a>

#### [a-name-filter-narrows-the-answer-to-that-channel](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

a get filtered by the name of one of two channels brings back only that channel

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.search_channels: user-1 gets channels filtered by the name wanted-1

Then

- only the one channel matching the filter comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-an-enabled-filter-leaves-only-the-enabled-channels"></a>

#### [an-enabled-filter-leaves-only-the-enabled-channels](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

with active and inactive channels mixed, a get filtered by enabled brings back only the active ones

Given

- one active webhook channel and one inactive channel, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Webhook channel channel-2: sends to https://hooks.example.test/notify, inactive

When

- NotificationAdapter.search_channels: user-1 gets channels filtered by enabled

Then

- only the channels that must appear in the response come back
  - items = ['channel-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-asking-for-the-first-channel-only-says-there-is-a-next-page"></a>

#### [asking-for-the-first-channel-only-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

with two channels, asking for only the first item brings one item back and the response says there is a next page

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.search_channels: user-1 gets only the first item

Then

- the first page holding one item comes back
  - len(items) = 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching_channels-the-monitor-searches-channels-like-the-superadmin"></a>

#### [the-monitor-searches-channels-like-the-superadmin](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

when the monitor gets without a filter, it receives the same response as the superadmin

Given

- two webhook channels and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.search_channels: user-1 gets every channel without a filter

Then

- only the channels that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-the-superadmin-counts-every-channel-laid"></a>

#### [the-superadmin-counts-every-channel-laid](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

with two channels, a get without a filter brings both of them back

Given

- two webhook channels and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.search_channels: user-1 gets every channel without a filter

Then

- only the channels that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_channels-a-user-who-is-not-the-superadmin-may-not-search-channels"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-channels](/tests/scenario/bai_scenario/manager/notification/test_searching_channels.py): pass

when a user who is not the superadmin gets without a filter, it is rejected for an insufficient role

Given

- two webhook channels and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel wanted-1: sends to https://hooks.example.test/notify
  - Webhook channel other-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.search_channels: user-1 gets every channel without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_rules

<a id="searching_rules-a-name-filter-narrows-the-answer-to-that-rule"></a>

#### [a-name-filter-narrows-the-answer-to-that-rule](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

a get filtered by the name of one of two rules brings back only that rule

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.search_rules: user-1 gets rules filtered by the name wanted-1

Then

- only the one rule matching the filter comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-a-rule-type-filter-narrows-the-answer-to-that-kind"></a>

#### [a-rule-type-filter-narrows-the-answer-to-that-kind](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

a get filtered by the type of one of two rules with different types brings back only that rule

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.terminated events

When

- NotificationAdapter.search_rules: user-1 gets rules filtered by the type session.started

Then

- only the one rule matching the filter comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-an-enabled-filter-leaves-only-the-enabled-rules"></a>

#### [an-enabled-filter-leaves-only-the-enabled-rules](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

with active and inactive rules mixed, a get filtered by enabled brings back only the active ones

Given

- one active rule and one inactive rule, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events
  - Rule rule-2: announces session.started events, inactive

When

- NotificationAdapter.search_rules: user-1 gets rules filtered by enabled

Then

- only the rules that must appear in the response come back
  - items = ['rule-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-the-monitor-searches-rules-like-the-superadmin"></a>

#### [the-monitor-searches-rules-like-the-superadmin](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

when the monitor gets without a filter, it receives the same response as the superadmin

Given

- two rules pointing at the same webhook channel and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.search_rules: user-1 gets every rule without a filter

Then

- only the rules that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-the-superadmin-counts-every-rule-laid"></a>

#### [the-superadmin-counts-every-rule-laid](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

with two rules, a get without a filter brings both of them back

Given

- two rules pointing at the same webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.search_rules: user-1 gets every rule without a filter

Then

- only the rules that must appear in the response come back
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_rules-a-user-who-is-not-the-superadmin-may-not-search-rules"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-rules](/tests/scenario/bai_scenario/manager/notification/test_searching_rules.py): pass

when a user who is not the superadmin gets without a filter, it is rejected for an insufficient role

Given

- two rules pointing at the same webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule wanted-1: announces session.started events
  - Rule other-1: announces session.started events

When

- NotificationAdapter.search_rules: user-1 gets every rule without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update_channel

<a id="editing_channels-an-edit-naming-no-field-changes-nothing"></a>

#### [an-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

editing without naming any field brings the channel back unchanged

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, naming no field

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_channels-changing-a-webhook-spec-moves-the-channel-to-the-new-url"></a>

#### [changing-a-webhook-spec-moves-the-channel-to-the-new-url](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when the spec of a webhook channel moves to another URL, the channel comes back with the new URL

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, moving the URL to https://hooks.example.test/elsewhere

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/elsewhere'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_channels-clearing-a-channel-description-leaves-it-empty"></a>

#### [clearing-a-channel-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when the description of a channel that has one is cleared, the channel comes back with an empty description

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, clearing the description

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_channels-disabling-a-channel-answers-it-disabled"></a>

#### [disabling-a-channel-answers-it-disabled](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when an active channel is changed to disabled, a disabled channel comes back

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, setting enabled to False

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'channel-1'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = False
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_channels-the-superadmin-renaming-a-channel-leaves-the-rest"></a>

#### [the-superadmin-renaming-a-channel-leaves-the-rest](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when the superadmin changes only the name, the whole channel comes back with the new name and everything else unchanged

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, renaming it to renamed

Then

- the whole channel created in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = None
  - channel_type = 'webhook'
  - spec.channel_type = <NotificationChannelTypeDTO.WEBHOOK: 'webhook'>
  - spec.url = 'https://hooks.example.test/notify'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_channels-a-user-granted-nothing-may-not-edit-a-channel"></a>

#### [a-user-granted-nothing-may-not-edit-a-channel](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when a user granted nothing changes the name, it is rejected for not enough permission

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, renaming it to by-a-user

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing_channels-an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused"></a>

#### [an-edit-with-a-spec-naming-neither-webhook-nor-email-is-refused](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

editing a channel with a spec naming neither webhook nor email is rejected as invalid input

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits the channel channel-1, giving an empty spec

Then

- the call is rejected
  - rejected: InvalidNotificationSpec

<a id="editing_channels-the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_editing_channels.py): pass

when the superadmin edits an id nothing answers to, it is rejected because no target is found

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.update_channel: user-1 edits an unknown id, renaming it to nowhere

Then

- the call is rejected
  - rejected: EntityNotFoundError

### update_rule

<a id="editing_rules-a-rule-edit-naming-no-field-changes-nothing"></a>

#### [a-rule-edit-naming-no-field-changes-nothing](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

editing without naming any field brings the rule back unchanged

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, naming no field

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_rules-changing-a-rule-template-answers-the-new-template"></a>

#### [changing-a-rule-template-answers-the-new-template](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when the template of a rule changes, the rule comes back with the new template

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, giving a new template

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = '{{ session_id }} started'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_rules-clearing-a-rule-description-leaves-it-empty"></a>

#### [clearing-a-rule-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when the description of a rule that has one is cleared, the rule comes back with an empty description

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, clearing the description

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_rules-disabling-a-rule-answers-it-disabled"></a>

#### [disabling-a-rule-answers-it-disabled](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when an active rule is changed to disabled, a disabled rule comes back

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, setting enabled to False

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'rule-1'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = False
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_rules-the-superadmin-renaming-a-rule-leaves-the-rest"></a>

#### [the-superadmin-renaming-a-rule-leaves-the-rest](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when the superadmin changes only the name, the whole rule comes back with the new name and everything else unchanged

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, renaming it to renamed

Then

- the whole rule created in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = None
  - rule_type = 'session.started'
  - channel_id: same as the channel it points at
  - message_template = 'Session {{ session_name }} is {{ status }}'
  - enabled = True
  - created_by: same as the user who created it
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing_rules-a-user-granted-nothing-may-not-edit-a-rule"></a>

#### [a-user-granted-nothing-may-not-edit-a-rule](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when a user granted nothing changes the name, it is rejected for not enough permission

Given

- one rule and the webhook channel it points at, and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits the rule rule-1, renaming it to by-a-user

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing_rules-the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_editing_rules.py): pass

when the superadmin edits an id nothing answers to, it is rejected because no target is found

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.update_rule: user-1 edits an unknown id, renaming it to nowhere

Then

- the call is rejected
  - rejected: EntityNotFoundError

### validate_channel

<a id="validating_channels-the-superadmin-validates-a-webhook-channel"></a>

#### [the-superadmin-validates-a-webhook-channel](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py): pass

with one webhook channel, when the superadmin validates it with a test message, the id of the validated channel comes back

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.validate_channel: user-1 validates the channel channel-1 with a test message

Then

- the id of the validated channel comes back
  - id: same as the channel created in advance

<a id="validating_channels-a-user-granted-nothing-may-not-validate-a-channel"></a>

#### [a-user-granted-nothing-may-not-validate-a-channel](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py): pass

when a user granted nothing validates a channel, it is rejected for not enough permission

Given

- one webhook channel and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.validate_channel: user-1 validates the channel channel-1 with a test message

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="validating_channels-the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-validating-a-channel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_validating_channels.py): pass

when the superadmin validates an id nothing answers to, it is rejected because no target is found

Given

- one webhook channel and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify

When

- NotificationAdapter.validate_channel: user-1 validates an unknown id with a test message

Then

- the call is rejected
  - rejected: NotificationChannelNotFound

### validate_rule

<a id="validating_rules-the-superadmin-validates-a-rule-with-test-data"></a>

#### [the-superadmin-validates-a-rule-with-test-data](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py): pass

with one session-started rule, when the superadmin validates it with test data of that type, the string made by putting the data into the template comes back

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.validate_rule: user-1 validates the rule rule-1 with test data

Then

- the string made by putting the data into the template comes back
  - message = 'Session train is running'

<a id="validating_rules-a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused"></a>

#### [a-rule-pointing-at-a-channel-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py): pass

validating a rule pointing at an unknown channel id is rejected because no channel is found

Given

- one rule pointing at an unknown channel id and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule orphan-rule-1: refers to a channel id no row answers to

When

- NotificationAdapter.validate_rule: user-1 validates the rule orphan-rule-1 with test data

Then

- the call is rejected
  - rejected: NotificationChannelNotFound

<a id="validating_rules-a-user-granted-nothing-may-not-validate-a-rule"></a>

#### [a-user-granted-nothing-may-not-validate-a-rule](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py): pass

when a user granted nothing validates a rule, it is rejected for not enough permission

Given

- one rule and the webhook channel it points at, and one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.validate_rule: user-1 validates the rule rule-1 with test data

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="validating_rules-the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-validating-a-rule-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/notification/test_validating_rules.py): pass

when the superadmin validates an id nothing answers to, it is rejected because no target is found

Given

- one rule and the webhook channel it points at, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Webhook channel channel-1: sends to https://hooks.example.test/notify
  - Rule rule-1: announces session.started events

When

- NotificationAdapter.validate_rule: user-1 validates an unknown id with test data

Then

- the call is rejected
  - rejected: NotificationRuleNotFound

