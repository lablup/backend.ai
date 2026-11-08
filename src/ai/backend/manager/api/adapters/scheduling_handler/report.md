## scheduling_handler

[adapter](/src/ai/backend/manager/api/adapters/scheduling_handler/adapter.py)

Scenario: complete

- no Action (1)
  - list_scheduling_handlers: success present 2 · rejection absent

**list_scheduling_handlers**

| scenario | verdict |
|---|---|
| [when the coordinator has registered no handler, an empty list comes back](#listing-no-registered-handler-lists-nothing) | answered |
| [the handlers the coordinator registered come back with name, category and description](#listing-the-registered-handlers-are-listed) | answered |

### list_scheduling_handlers

<a id="listing-no-registered-handler-lists-nothing"></a>

#### [no-registered-handler-lists-nothing](/tests/scenario/bai_scenario/manager/scheduling_handler/test_listing.py): pass

when the coordinator has registered no handler, an empty list comes back

Given

- the coordinator has registered no handler

When

- SchedulingHandlerAdapter.list_scheduling_handlers: lists the scheduling handlers

Then

- an empty list comes back
  - items = []

<a id="listing-the-registered-handlers-are-listed"></a>

#### [the-registered-handlers-are-listed](/tests/scenario/bai_scenario/manager/scheduling_handler/test_listing.py): pass

the handlers the coordinator registered come back with name, category and description

Given

- the coordinator has registered a replica check handler and a deploying initialization handler

When

- SchedulingHandlerAdapter.list_scheduling_handlers: lists the scheduling handlers

Then

- each handler comes back in registration order with its name, category and the first line of its description
  - items = [SchedulingHandlerNode(name='check-replica-deployments', category=<SchedulingHandlerCategory.SCALING: 'scaling'>, description='Handler for checking and managing deployment replicas.'), SchedulingHandlerNode(name='deploying-initializing', category=<SchedulingHandlerCategory.LIFECYCLE: 'lifecycle'>, description='DEPLOYING / INITIALIZING: register the appproxy endpoint for deployments that entered')]

