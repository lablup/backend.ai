# Background Task Handler System

← [Back to Common Package](../README.md)

## Overview

The Background Task Handler system is a framework for asynchronously processing long-running tasks in Backend.AI. It issues Task IDs to track tasks and notifies upon completion via events.

## Architecture

```
┌──────────────────────────────────────┐
│    BackgroundTaskManager             │
│                                      │
│  - Task execution and management     │
│  - Task metadata storage (Redis)     │
│  - Event publishing                  │
│  - Heartbeat and retry logic         │
└───────────┬──────────────────────────┘
            │
            ├─→ Task Registry  (task registration)
            ├─→ Task Hooks     (middleware processing)
            └─→ ProgressReporter (progress reporting)
                     │
                     ↓
            ┌────────────────────┐
            │   Redis Storage    │ Metadata storage (recoverable)
            └────────────────────┘
                     │
                     ↓
            ┌────────────────────┐
            │  Event Producer    │ Publish success/failure events
            └────────────────────┘
```

## Key Components

### 1. BackgroundTaskManager

Central manager that manages all background tasks.

**Key Features:**
- Task startup and execution management
- Store task metadata in Valkey for recovery after server restart or failure
- Publish task success/failure events to support monitoring by other components and users
- Task status tracking via heartbeat
- Retry failed tasks
- Task cancellation and cleanup

### 2. Task Types

#### LocalBgtask
Planned for deprecation.

#### SingleBgtask
Single task that can be retried on failure.

**Characteristics:**
- Store metadata in Valkey
- Retriable (`retriable() = True`)
- Progress tracking available

**Usage Examples:**
- Image pulling tasks (requires progress tracking)
- Large-scale data cleanup tasks
- Long-running tasks

#### ParallelBgtask
Executes multiple tasks in parallel.

**Characteristics:**
- Only failed tasks can be retried when some tasks fail
- Individual progress tracking of some tasks via event subscription
- Execute multiple subtasks in parallel
- Independent progress tracking for each subtask

**Usage Examples:**
- Check the status of multiple agents simultaneously
- Split large-scale session cleanup tasks into batches and execute them

### 3. Task Hooks

Hooks executed before and after task execution handle additional features such as:

- Task execution metric collection (start and completion time, success and failure count, and so on)
- Publish task state change events
- Clean up Valkey metadata on task completion

### 4. Task Registry

Registry that registers and manages task handlers.

## Task Lifecycle

Tasks are created in `ONGOING` state immediately upon registration. There is no PENDING state.

```
┌──────────┐
│ ONGOING  │ Task registration and execution start
└────┬─────┘
     │
     ├─→ Success ─→ ┌──────────┐
     │              │ SUCCESS  │
     │              └──────────┘
     │
     ├─→ Failure ─→ ┌──────────┐
     │              │ FAILURE  │ No more retries
     │              └──────────┘
     │
     └─→ Cancel ─→ ┌───────────┐
                   │ CANCELLED │
                   └───────────┘
```

**Retry Mechanism**:
- `FAILURE` state is the final failure state with no retries
- Retries only apply to tasks that remain in `ONGOING` state but are no longer managed due to server restarts and so on

## State Management

### Task States

- `ONGOING`: Task executing
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed
- `CANCELLED`: Task cancelled

### Heartbeat

The BackgroundTaskManager sends heartbeats for running tasks periodically. If a heartbeat is not updated for a certain period, the task can be retried by another server capable of performing it.

## Valkey Metadata Storage

Task metadata is stored in Valkey and used for recovery and monitoring upon server restart.

## Event Publishing

Events are published via Event Dispatcher when task state changes.

### Published Events

#### BgtaskUpdatedEvent
Published when task progress is updated.

#### BgtaskDoneEvent
Published when task completes successfully.

#### BgtaskFailedEvent
Published when task fails.

#### BgtaskCancelledEvent
Published when task is cancelled.

## Performance Considerations

### Batch Processing

When processing a large number of items, divide them into batches.

## Related documents

- [Event Dispatcher System](../events/README.md) - Event publishing and subscription
- [Manager services](../../manager/services/README.md) - Using background tasks in services
- [Storage proxy background tasks](../../storage/bgtask/) - Storage proxy background tasks

## Reference materials

### Task Type Selection Guide

| Requirement | Recommended Task Type | Reason |
|------------|----------------------|--------|
| Retry needed | SingleBgtask | Can retry on failure |
| Parallel processing needed | ParallelBgtask | Execute multiple tasks at the same time |
| Progress tracking needed | SingleBgtask/ParallelBgtask | Progress tracking available |
| Long-running tasks | SingleBgtask/ParallelBgtask | Status tracking via heartbeat |
