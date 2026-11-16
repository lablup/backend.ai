## entity_share

[adapter](/src/ai/backend/manager/api/adapters/entity_share/adapter.py)

Scenario: complete

- built from ops (4)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - my_search: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
- direct implementation (6)
  - accept: success present 1 · rejection present 1 (scope)
  - cancel: success present 1 · rejection present 1 (single_entity)
  - create: success present 1 · rejection present 1 (scope)
  - leave: success present 1 · rejection present 1 (scope)
  - reject: success present 1 · rejection present 1 (scope)
  - revoke: success present 1 · rejection present 1 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted share reading in the project loads one by id, the share comes back as a node](#reading-a-user-granted-on-the-project-loads-the-share) | answered |
| [a read by id is checked, so an id nothing answers to comes back as a denial rather than an empty value](#reading-an-unknown-share-id-answers-a-denial) | answered |
| [when a user granted nothing loads one by id, that entry is rejected for lack of permission](#reading-a-user-granted-nothing-gets-a-denial-for-the-share) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted share reading in the project reads the share, the whole share comes back](#reading-a-user-granted-on-the-project-reads-the-share) | answered |
| [when a user granted nothing reads the share, the call is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-the-share) | rejected |

**my_search**

| scenario | verdict |
|---|---|
| [when a user who can read shares in their own scope pages through the ones addressed to them, the offer they sent and an offer between others are left out and only that share comes back as one page](#searching-the-recipient-pages-through-the-shares-addressed-to-them) | answered |
| [when a user granted nothing pages through the shares addressed to them, the call is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-page-through-their-shares) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user who can read shares in the project pages through a folder filtered by recipient, the offer of another folder and the offer to someone else are left out and only that share comes back as one page](#searching-the-sharer-pages-through-the-shares-of-a-folder) | answered |
| [when a user granted nothing pages through a folder, the call is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-page-through-a-folders-shares) | rejected |

**accept**

| scenario | verdict |
|---|---|
| [when a user who can answer shares in their own scope accepts the offer, the accepted share comes back whole](#answering-the-recipient-accepts-the-offer) | answered |
| [when a user granted nothing accepts the offer, the call is rejected for lack of permission](#answering-a-user-granted-nothing-may-not-accept-the-offer) | rejected |

**cancel**

| scenario | verdict |
|---|---|
| [when the lending side cancels the unanswered offer, the canceled share comes back whole](#withdrawing-the-sharer-cancels-the-unanswered-offer) | answered |
| [when a user granted nothing cancels the offer, the call is rejected for lack of permission](#withdrawing-a-user-granted-nothing-may-not-cancel-the-offer) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted share creation in the project offers the folder to another person, the unanswered share comes back whole](#creating-a-user-granted-on-the-project-offers-the-folder) | answered |
| [when a user granted nothing offers the folder, the call is rejected for lack of permission](#creating-a-user-granted-nothing-cannot-offer-the-folder) | rejected |

**leave**

| scenario | verdict |
|---|---|
| [when the receiving side leaves the share in their own scope, the revoked share comes back whole](#withdrawing-the-recipient-leaves-the-share) | answered |
| [when a user granted nothing leaves the share, the call is rejected for lack of permission](#withdrawing-a-user-granted-nothing-may-not-leave-the-share) | rejected |

**reject**

| scenario | verdict |
|---|---|
| [when a user who can answer shares in their own scope rejects the offer, the rejected share comes back whole](#answering-the-recipient-rejects-the-offer) | answered |
| [when a user granted nothing rejects the offer, the call is rejected for lack of permission](#answering-a-user-granted-nothing-may-not-reject-the-offer) | rejected |

**revoke**

| scenario | verdict |
|---|---|
| [when the lending side takes back the share, the revoked share comes back whole](#withdrawing-the-sharer-takes-back-the-share) | answered |
| [when a user granted nothing takes the share back, the call is rejected for lack of permission](#withdrawing-a-user-granted-nothing-may-not-take-the-share-back) | rejected |

### batch_load_by_ids

<a id="reading-a-user-granted-on-the-project-loads-the-share"></a>

#### [a-user-granted-on-the-project-loads-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

when a user granted share reading in the project loads one by id, the share comes back as a node

Given

- one project folder with an offer to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.batch_load_by_ids: user-1 loads one share at once

Then

- the share laid in advance comes back as a node
  - length = 1
  - [0].sharer_user_id: same as the id of the person lending the folder
  - [0].recipient_entity_type = 'user'
  - [0].recipient_entity_id: same as the id of the person the folder is lent to
  - [0].recipient_email = None
  - [0].target_entity_type = 'vfolder'
  - [0].target_entity_id: same as the id of the folder laid in advance
  - [0].permissions = []
  - [0].status = 'pending'
  - [0].expires_at = None
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [0].id: same as the id of the share laid in advance
  - [0].entity_id: same as the id of the share laid in advance

<a id="reading-an-unknown-share-id-answers-a-denial"></a>

#### [an-unknown-share-id-answers-a-denial](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

a read by id is checked, so an id nothing answers to comes back as a denial rather than an empty value

Given

- one project folder with an offer to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.batch_load_by_ids: user-1 loads one share and one unknown id at once

Then

- the share laid in advance comes back as a node and the unknown id entry is rejected for lack of permission
  - length = 2
  - [0].sharer_user_id: same as the id of the person lending the folder
  - [0].recipient_entity_type = 'user'
  - [0].recipient_entity_id: same as the id of the person the folder is lent to
  - [0].recipient_email = None
  - [0].target_entity_type = 'vfolder'
  - [0].target_entity_id: same as the id of the folder laid in advance
  - [0].permissions = []
  - [0].status = 'pending'
  - [0].expires_at = None
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [0].id: same as the id of the share laid in advance
  - [0].entity_id: same as the id of the share laid in advance
  - [1] denied = 'NotEnoughPermission'

<a id="reading-a-user-granted-nothing-gets-a-denial-for-the-share"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

when a user granted nothing loads one by id, that entry is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.batch_load_by_ids: user-3 loads one share at once

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-on-the-project-reads-the-share"></a>

#### [a-user-granted-on-the-project-reads-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

when a user granted share reading in the project reads the share, the whole share comes back

Given

- one project folder with an offer to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.get: user-1 reads the share of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'pending'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="reading-a-user-granted-nothing-may-not-read-the-share"></a>

#### [a-user-granted-nothing-may-not-read-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_reading.py): pass

when a user granted nothing reads the share, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.get: user-3 reads the share of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_search

<a id="searching-the-recipient-pages-through-the-shares-addressed-to-them"></a>

#### [the-recipient-pages-through-the-shares-addressed-to-them](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

when a user who can read shares in their own scope pages through the ones addressed to them, the offer they sent and an offer between others are left out and only that share comes back as one page

Given

- one more folder outside the scope whose offer the recipient makes, one offer of the same folder to a third person, one project folder with an offer to another person, and the person the folder is lent to
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet
  - Project vfolder other-folder-1: is placed in the project and is ready to use
  - vfolder share offer other-share-1: offered with no ceiling on the permissions, not answered yet
  - vfolder share offer bystander-share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.my_search: user-2 pages through the shares of their own side

Then

- the share laid in advance comes back whole
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].sharer_user_id: same as the id of the person lending the folder
  - items[0].recipient_entity_type = 'user'
  - items[0].recipient_entity_id: same as the id of the person the folder is lent to
  - items[0].recipient_email = None
  - items[0].target_entity_type = 'vfolder'
  - items[0].target_entity_id: same as the id of the folder laid in advance
  - items[0].permissions = []
  - items[0].status = 'pending'
  - items[0].expires_at = None
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: same as the id of the share laid in advance
  - items[0].entity_id: same as the id of the share laid in advance

<a id="searching-a-user-granted-nothing-may-not-page-through-their-shares"></a>

#### [a-user-granted-nothing-may-not-page-through-their-shares](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

when a user granted nothing pages through the shares addressed to them, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.my_search: user-3 pages through the shares of their own side

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-the-sharer-pages-through-the-shares-of-a-folder"></a>

#### [the-sharer-pages-through-the-shares-of-a-folder](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

when a user who can read shares in the project pages through a folder filtered by recipient, the offer of another folder and the offer to someone else are left out and only that share comes back as one page

Given

- one more folder outside the scope whose offer the recipient makes, one offer of the same folder to a third person, one project folder with an offer to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet
  - Project vfolder other-folder-1: is placed in the project and is ready to use
  - vfolder share offer other-share-1: offered with no ceiling on the permissions, not answered yet
  - vfolder share offer bystander-share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.scoped_search: user-1 pages through the shares of folder folder-1 addressed to user-2

Then

- the share laid in advance comes back whole
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].sharer_user_id: same as the id of the person lending the folder
  - items[0].recipient_entity_type = 'user'
  - items[0].recipient_entity_id: same as the id of the person the folder is lent to
  - items[0].recipient_email = None
  - items[0].target_entity_type = 'vfolder'
  - items[0].target_entity_id: same as the id of the folder laid in advance
  - items[0].permissions = []
  - items[0].status = 'pending'
  - items[0].expires_at = None
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: same as the id of the share laid in advance
  - items[0].entity_id: same as the id of the share laid in advance

<a id="searching-a-user-granted-nothing-may-not-page-through-a-folders-shares"></a>

#### [a-user-granted-nothing-may-not-page-through-a-folders-shares](/tests/scenario/bai_scenario/manager/entity_share/test_searching.py): pass

when a user granted nothing pages through a folder, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.scoped_search: user-3 pages through the shares of folder folder-1 addressed to user-2

Then

- the call is rejected
  - rejected: NotEnoughPermission

### accept

<a id="answering-the-recipient-accepts-the-offer"></a>

#### [the-recipient-accepts-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

when a user who can answer shares in their own scope accepts the offer, the accepted share comes back whole

Given

- one project folder with an offer to another person, and the person the folder is lent to
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.accept: user-2 accepts the offer of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'accepted'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="answering-a-user-granted-nothing-may-not-accept-the-offer"></a>

#### [a-user-granted-nothing-may-not-accept-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

when a user granted nothing accepts the offer, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.accept: user-3 accepts the offer of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### cancel

<a id="withdrawing-the-sharer-cancels-the-unanswered-offer"></a>

#### [the-sharer-cancels-the-unanswered-offer](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when the lending side cancels the unanswered offer, the canceled share comes back whole

Given

- one project folder with an offer to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.cancel: user-1 cancels the unanswered offer of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'canceled'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="withdrawing-a-user-granted-nothing-may-not-cancel-the-offer"></a>

#### [a-user-granted-nothing-may-not-cancel-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when a user granted nothing cancels the offer, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.cancel: user-3 cancels the unanswered offer of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create

<a id="creating-a-user-granted-on-the-project-offers-the-folder"></a>

#### [a-user-granted-on-the-project-offers-the-folder](/tests/scenario/bai_scenario/manager/entity_share/test_creating.py): pass

when a user granted share creation in the project offers the folder to another person, the unanswered share comes back whole

Given

- one project folder and two people, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project

When

- EntityShareAdapter.create: user-1 offers folder folder-1 to user-2

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'pending'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: skipped: the database generates it
  - entity_id: same as the id of the share in the same answer

<a id="creating-a-user-granted-nothing-cannot-offer-the-folder"></a>

#### [a-user-granted-nothing-cannot-offer-the-folder](/tests/scenario/bai_scenario/manager/entity_share/test_creating.py): pass

when a user granted nothing offers the folder, the call is rejected for lack of permission

Given

- one project folder and two people, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project

When

- EntityShareAdapter.create: user-3 offers folder folder-1 to user-2

Then

- the call is rejected
  - rejected: NotEnoughPermission

### leave

<a id="withdrawing-the-recipient-leaves-the-share"></a>

#### [the-recipient-leaves-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when the receiving side leaves the share in their own scope, the revoked share comes back whole

Given

- one project folder with a share lent to another person, and the person the folder is lent to
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet
  - vfolder share offer share-1: the recipient accepts it

When

- EntityShareAdapter.leave: user-2 leaves the share it took of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'revoked'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="withdrawing-a-user-granted-nothing-may-not-leave-the-share"></a>

#### [a-user-granted-nothing-may-not-leave-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when a user granted nothing leaves the share, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.leave: user-3 leaves the share it took of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### reject

<a id="answering-the-recipient-rejects-the-offer"></a>

#### [the-recipient-rejects-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

when a user who can answer shares in their own scope rejects the offer, the rejected share comes back whole

Given

- one project folder with an offer to another person, and the person the folder is lent to
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.reject: user-2 rejects the offer of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'rejected'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="answering-a-user-granted-nothing-may-not-reject-the-offer"></a>

#### [a-user-granted-nothing-may-not-reject-the-offer](/tests/scenario/bai_scenario/manager/entity_share/test_answering.py): pass

when a user granted nothing rejects the offer, the call is rejected for lack of permission

Given

- one project folder with an offer to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet

When

- EntityShareAdapter.reject: user-3 rejects the offer of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### revoke

<a id="withdrawing-the-sharer-takes-back-the-share"></a>

#### [the-sharer-takes-back-the-share](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when the lending side takes back the share, the revoked share comes back whole

Given

- one project folder with a share lent to another person, and the person lending the folder
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet
  - vfolder share offer share-1: the recipient accepts it

When

- EntityShareAdapter.revoke: user-1 takes back the share it lent of folder folder-1

Then

- the whole share comes back
  - sharer_user_id: same as the id of the person lending the folder
  - recipient_entity_type = 'user'
  - recipient_entity_id: same as the id of the person the folder is lent to
  - recipient_email = None
  - target_entity_type = 'vfolder'
  - target_entity_id: same as the id of the folder laid in advance
  - permissions = []
  - status = 'revoked'
  - expires_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the id of the share laid in advance
  - entity_id: same as the id of the share laid in advance

<a id="withdrawing-a-user-granted-nothing-may-not-take-the-share-back"></a>

#### [a-user-granted-nothing-may-not-take-the-share-back](/tests/scenario/bai_scenario/manager/entity_share/test_withdrawing.py): pass

when a user granted nothing takes the share back, the call is rejected for lack of permission

Given

- one project folder with a share lent to another person, and someone unrelated
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare a user granted share permissions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role share-lender-1: applies only within the scope it is granted in
    - Role share-lender-1: CREATE allowed on every entity_share
    - Role share-lender-1: READ allowed on every entity_share
    - Role share-lender-1: SOFT_DELETE allowed on every entity_share
    - regular user user-1: holds Role share-lender-1
  - Prepare a user granted share permissions in their own scope
    - Role share-recipient-1: applies only within the scope it is granted in
    - Role share-recipient-1: READ allowed on every entity_share
    - regular user user-1: holds Role share-recipient-1
    - Role share-recipient-2: applies only within the scope it is granted in
    - Role share-recipient-2: READ allowed on every entity_share
    - Role share-recipient-2: UPDATE allowed on every entity_share
    - Role share-recipient-2: SOFT_DELETE allowed on every entity_share
    - regular user user-2: holds Role share-recipient-2
  - Project vfolder folder-1: is placed in the project and is ready to use
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - vfolder share offer share-1: offered with no ceiling on the permissions, not answered yet
  - vfolder share offer share-1: the recipient accepts it

When

- EntityShareAdapter.revoke: user-3 takes back the share it lent of folder folder-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

