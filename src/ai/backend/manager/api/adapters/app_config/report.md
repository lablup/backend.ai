## app_config

[background](/src/ai/backend/manager/api/adapters/app_config/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/app_config/adapter.py)

Scenario: incomplete 1 / 2

- direct implementation (2)
  - my_app_configs: success present 11 · rejection present 1 (scope)
  - public_app_configs: success present 5 · rejection absent (anonymous_scope): SCENARIO-GAP

**my_app_configs**

| scenario | verdict |
|---|---|
| [when the same name is named twice, the same value comes back twice](#reading_mine-a-name-asked-twice-is-answered-twice) | answered |
| [when a user granted read permission reads a name that has only a definition, with neither an allow list entry nor a fragment, the name is not left out of the answer and comes back as an empty config](#reading_mine-a-name-holding-no-fragment-answers-an-empty-config) | answered |
| [when a user granted read permission reads a name that has no definition at all, the call is not rejected for the missing definition and comes back as an empty config. This read does not check the definition and looks only at fragments](#reading_mine-a-name-nothing-registers-answers-an-empty-config) | answered |
| [when a name has a fragment only in the public scope and is read, the value of that fragment comes back as is](#reading_mine-a-public-fragment-alone-answers-its-own-value) | answered |
| [when the rank of the domain allow list entry is set higher than the user entry, the priority of overlapping keys in the same fragments flips to the domain. The rank lives on the allow list entry and the owner of the value cannot be changed](#reading_mine-a-rank-the-admin-flipped-lets-the-domains-fragment-override-mine) | answered |
| [even when another domain has a fragment for the same name, reading the user's own config brings back only the value of the user's own domain fragment](#reading_mine-another-domains-fragment-does-not-merge-into-mine) | answered |
| [even when another user in the same domain has a fragment for the same name, reading the user's own config brings back only the value of the user's own fragment](#reading_mine-another-users-fragment-does-not-merge-into-mine) | answered |
| [when the same name has both a domain fragment and the user's own fragment, and the allow list entry is at its default rank, the user's value stays for overlapping keys and both values stay for keys that do not overlap](#reading_mine-my-own-fragment-overrides-the-domains) | answered |
| [when three names are read in one call, each merged result comes back in the order requested](#reading_mine-several-names-answer-one-each-in-request-order) | answered |
| [when the same name has both a public fragment and a domain fragment, and the allow list entry is at its default rank, the domain value stays for overlapping keys](#reading_mine-the-domains-fragment-overrides-the-public-one) | answered |
| [turning permission enforcement off lets a user granted nothing read its own config](#reading_mine-turning-enforcement-off-lets-a-user-granted-nothing-read) | answered |
| [when a user granted nothing reads its own config, the scope permission check rejects the call for lack of permission](#reading_mine-a-user-granted-nothing-may-not-read-their-own-config) | rejected |

**public_app_configs**

| scenario | verdict |
|---|---|
| [when a name with public, domain, and user fragments is read without signing in, only the value of the public fragment comes back. The domain and user fragments do not merge in](#reading_public-a-caller-not-signed-in-reads-the-public-value-only) | answered |
| [when a name that has only a user fragment is read without signing in, an empty config comes back](#reading_public-a-name-holding-no-public-fragment-answers-an-empty-config) | answered |
| [when a name that has no definition at all is read without signing in, the same empty config comes back as for a name with no public fragment. This read cannot tell which names are registered](#reading_public-a-name-nothing-registers-answers-an-empty-config-too) | answered |
| [even when a user granted nothing reads the same three fragments through the public read while signed in, only the value of the public fragment comes back. This read does not look at the caller at all](#reading_public-a-signed-in-user-granted-nothing-gets-the-same-public-answer) | answered |
| [when three names are read in one call without signing in, each public value comes back in the order requested](#reading_public-several-names-answer-one-each-in-request-order) | answered |

### my_app_configs

<a id="reading_mine-a-name-asked-twice-is-answered-twice"></a>

#### [a-name-asked-twice-is-answered-twice](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when the same name is named twice, the same value comes back twice

Given

- one config name opened in the public scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1, config-1

Then

- the merged config comes back for every requested name
  - app_configs = 2
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}
  - app_configs[1].config_name: same as the requested name
  - app_configs[1].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

<a id="reading_mine-a-name-holding-no-fragment-answers-an-empty-config"></a>

#### [a-name-holding-no-fragment-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when a user granted read permission reads a name that has only a definition, with neither an allow list entry nor a fragment, the name is not left out of the answer and comes back as an empty config

Given

- one config name opened in no scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in no scope
    - Config definition config-1: the config of this name is registered

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {}

<a id="reading_mine-a-name-nothing-registers-answers-an-empty-config"></a>

#### [a-name-nothing-registers-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when a user granted read permission reads a name that has no definition at all, the call is not rejected for the missing definition and comes back as an empty config. This read does not check the definition and looks only at fragments

Given

- an unregistered config name, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for unregistered

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {}

<a id="reading_mine-a-public-fragment-alone-answers-its-own-value"></a>

#### [a-public-fragment-alone-answers-its-own-value](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when a name has a fragment only in the public scope and is read, the value of that fragment comes back as is

Given

- one config name opened in the public scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

<a id="reading_mine-a-rank-the-admin-flipped-lets-the-domains-fragment-override-mine"></a>

#### [a-rank-the-admin-flipped-lets-the-domains-fragment-override-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when the rank of the domain allow list entry is set higher than the user entry, the priority of overlapping keys in the same fragments flips to the domain. The rank lives on the allow list entry and the owner of the value cannot be changed

Given

- one config name opened in the domain, user scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the domain, user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank 400
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment domain-fragment-1: value {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - app config fragment own-fragment-1: value {'theme': 'solar', 'menu': {'home': False}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'dark', 'menu': {'home': False, 'docs': False, 'billing': True}}

<a id="reading_mine-another-domains-fragment-does-not-merge-into-mine"></a>

#### [another-domains-fragment-does-not-merge-into-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

even when another domain has a fragment for the same name, reading the user's own config brings back only the value of the user's own domain fragment

Given

- one config name opened in the domain scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - app config fragment domain-fragment-1: value {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - Domain away-1
  - app config fragment other-domains-fragment-1: value {'theme': 'elsewhere'}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}

<a id="reading_mine-another-users-fragment-does-not-merge-into-mine"></a>

#### [another-users-fragment-does-not-merge-into-mine](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

even when another user in the same domain has a fragment for the same name, reading the user's own config brings back only the value of the user's own fragment

Given

- one config name opened in the user scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'solar', 'menu': {'home': False}}
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - app config fragment anothers-fragment-1: value {'theme': 'theirs', 'secret': 1}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'solar', 'menu': {'home': False}}

<a id="reading_mine-my-own-fragment-overrides-the-domains"></a>

#### [my-own-fragment-overrides-the-domains](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when the same name has both a domain fragment and the user's own fragment, and the allow list entry is at its default rank, the user's value stays for overlapping keys and both values stay for keys that do not overlap

Given

- one config name opened in the domain, user scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the domain, user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the domain scope, rank is the default of the scope kind
    - Allow-list entry entry-2: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment domain-fragment-1: value {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}
  - app config fragment own-fragment-1: value {'theme': 'solar', 'menu': {'home': False}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'solar', 'menu': {'docs': False, 'billing': True, 'home': False}}

<a id="reading_mine-several-names-answer-one-each-in-request-order"></a>

#### [several-names-answer-one-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when three names are read in one call, each merged result comes back in the order requested

Given

- 3 config names each holding a public config fragment, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Config definition config-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Config definition config-3: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'n': 1}
  - public app config fragment public-fragment-2: value {'n': 2}
  - public app config fragment public-fragment-3: value {'n': 3}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1, config-2, config-3

Then

- the merged config comes back for every requested name
  - app_configs = 3
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'n': 1}
  - app_configs[1].config_name: same as the requested name
  - app_configs[1].config = {'n': 2}
  - app_configs[2].config_name: same as the requested name
  - app_configs[2].config = {'n': 3}

<a id="reading_mine-the-domains-fragment-overrides-the-public-one"></a>

#### [the-domains-fragment-overrides-the-public-one](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when the same name has both a public fragment and a domain fragment, and the allow list entry is at its default rank, the domain value stays for overlapping keys

Given

- one config name opened in the public, domain scope, and one user granted the config read permission in their own scope
  - Domain home-1
  - Prepare a user granted the READ permission on config in their own scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role own-scope-1: applies only within the scope it is granted in
    - Role own-scope-1: READ allowed on every app_config
    - regular user user-1: holds Role own-scope-1
  - Prepare a config name opened in the public, domain scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Allow-list entry entry-2: the config of this name can be set in the domain scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True, 'docs': True}}
  - app config fragment domain-fragment-1: value {'theme': 'dark', 'menu': {'docs': False, 'billing': True}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'dark', 'menu': {'home': True, 'docs': False, 'billing': True}}

<a id="reading_mine-turning-enforcement-off-lets-a-user-granted-nothing-read"></a>

#### [turning-enforcement-off-lets-a-user-granted-nothing-read](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

turning permission enforcement off lets a user granted nothing read its own config

Given

- one config name opened in the public scope, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True, 'docs': True}}

<a id="reading_mine-a-user-granted-nothing-may-not-read-their-own-config"></a>

#### [a-user-granted-nothing-may-not-read-their-own-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_mine.py): pass

when a user granted nothing reads its own config, the scope permission check rejects the call for lack of permission

Given

- one config name opened in the public scope, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True, 'docs': True}}

When

- AppConfigAdapter.my_app_configs: user-1 reads its own config for config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### public_app_configs

<a id="reading_public-a-caller-not-signed-in-reads-the-public-value-only"></a>

#### [a-caller-not-signed-in-reads-the-public-value-only](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py): pass

when a name with public, domain, and user fragments is read without signing in, only the value of the public fragment comes back. The domain and user fragments do not merge in

Given

- one config name opened in the public, domain, user scope, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public, domain, user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Allow-list entry entry-2: the config of this name can be set in the domain scope, rank is the default of the scope kind
    - Allow-list entry entry-3: the config of this name can be set in the user scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True}}
  - app config fragment domain-fragment-1: value {'theme': 'dark'}
  - app config fragment own-fragment-1: value {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs: a caller who is not signed in reads the public config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True}}

<a id="reading_public-a-name-holding-no-public-fragment-answers-an-empty-config"></a>

#### [a-name-holding-no-public-fragment-answers-an-empty-config](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py): pass

when a name that has only a user fragment is read without signing in, an empty config comes back

Given

- one config name opened in the user scope, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the user scope, rank is the default of the scope kind
  - app config fragment own-fragment-1: value {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs: a caller who is not signed in reads the public config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {}

<a id="reading_public-a-name-nothing-registers-answers-an-empty-config-too"></a>

#### [a-name-nothing-registers-answers-an-empty-config-too](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py): pass

when a name that has no definition at all is read without signing in, the same empty config comes back as for a name with no public fragment. This read cannot tell which names are registered

Given

- an unregistered config name, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project

When

- AppConfigAdapter.public_app_configs: a caller who is not signed in reads the public config for unregistered

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {}

<a id="reading_public-a-signed-in-user-granted-nothing-gets-the-same-public-answer"></a>

#### [a-signed-in-user-granted-nothing-gets-the-same-public-answer](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py): pass

even when a user granted nothing reads the same three fragments through the public read while signed in, only the value of the public fragment comes back. This read does not look at the caller at all

Given

- one config name opened in the public, domain, user scope, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public, domain, user scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Allow-list entry entry-2: the config of this name can be set in the domain scope, rank is the default of the scope kind
    - Allow-list entry entry-3: the config of this name can be set in the user scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light', 'menu': {'home': True}}
  - app config fragment domain-fragment-1: value {'theme': 'dark'}
  - app config fragment own-fragment-1: value {'theme': 'solar'}

When

- AppConfigAdapter.public_app_configs: user-1 reads the public config for config-1

Then

- the merged config comes back for every requested name
  - app_configs = 1
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'theme': 'light', 'menu': {'home': True}}

<a id="reading_public-several-names-answer-one-each-in-request-order"></a>

#### [several-names-answer-one-each-in-request-order](/tests/scenario/bai_scenario/manager/app_config/test_reading_public.py): pass

when three names are read in one call without signing in, each public value comes back in the order requested

Given

- 3 config names each holding a public config fragment, and one user with no config permission
  - Domain home-1
  - Prepare a user with no config permission
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
  - Prepare a config name opened in the public scope
    - Config definition config-1: the config of this name is registered
    - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Config definition config-2: the config of this name is registered
    - Allow-list entry entry-2: the config of this name can be set in the public scope, rank is the default of the scope kind
    - Config definition config-3: the config of this name is registered
    - Allow-list entry entry-3: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'n': 1}
  - public app config fragment public-fragment-2: value {'n': 2}
  - public app config fragment public-fragment-3: value {'n': 3}

When

- AppConfigAdapter.public_app_configs: a caller who is not signed in reads the public config for config-1, config-2, config-3

Then

- the merged config comes back for every requested name
  - app_configs = 3
  - app_configs[0].config_name: same as the requested name
  - app_configs[0].config = {'n': 1}
  - app_configs[1].config_name: same as the requested name
  - app_configs[1].config = {'n': 2}
  - app_configs[2].config_name: same as the requested name
  - app_configs[2].config = {'n': 3}

