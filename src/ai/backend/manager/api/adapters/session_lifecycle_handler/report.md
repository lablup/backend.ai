## session_lifecycle_handler

[background](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/session_lifecycle_handler/adapter.py)

Scenario: complete

- no Action (1)
  - list_session_lifecycle_handlers: success present 2 · rejection absent

**list_session_lifecycle_handlers**

| scenario | verdict |
|---|---|
| [when the coordinator has registered no handler, an empty list comes back](#listing-no-registered-handler-lists-nothing) | answered |
| [the handler the coordinator registered comes back with its name and description](#listing-the-registered-handler-is-listed) | answered |

### list_session_lifecycle_handlers

<a id="listing-no-registered-handler-lists-nothing"></a>

#### [no-registered-handler-lists-nothing](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py): pass

when the coordinator has registered no handler, an empty list comes back

Given

- the coordinator has registered no handler

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers: lists the session handlers

Then

- an empty list comes back
  - items = []

<a id="listing-the-registered-handler-is-listed"></a>

#### [the-registered-handler-is-listed](/tests/scenario/bai_scenario/manager/session_lifecycle_handler/test_listing.py): pass

the handler the coordinator registered comes back with its name and description

Given

- the coordinator has registered a session terminator handler

When

- SessionLifecycleHandlerAdapter.list_session_lifecycle_handlers: lists the session handlers

Then

- one session terminator handler comes back with its name and description
  - items = [SessionLifecycleHandlerNode(name='terminate-sessions', description='Terminates the kernels of sessions marked for termination.')]

