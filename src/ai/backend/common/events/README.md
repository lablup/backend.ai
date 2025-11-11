# Event Dispatcher System

← [Back to Common Package](../README.md)

## Overview

The Event Dispatcher system provides asynchronous event-based communication between Backend.AI components. This system is a unified framework for event publishing, subscription, and processing, enabling efficient communication while maintaining loose coupling between components.

**Important Notes:**
- Message production and delivery are not guaranteed. Messages may be lost, so caution is required.
- **Broadcast**: Attempts delivery to all subscribers, but message loss is possible. Use only for fast feedback, and it's recommended to use other mechanisms like polling for critical notifications.
- **Anycast**: Delivered to only one consumer in the consumer group. Use when the task can be performed on any single server among multiple servers (task distribution, load balancing).

## Architecture

```
┌──────────────────┐
│  EventProducer   │  Event publishing
│                  │
│  - produce()     │
└────────┬─────────┘
         │
         ↓ (Message Queue)
         │
┌────────┴─────────┐
│ EventDispatcher  │  Event consumption and routing
│                  │
│  - consume()     │  Anycast events (1:1)
│  - subscribe()   │  Broadcast events (1:N)
└────────┬─────────┘
         │
         ↓
┌────────┴─────────┐
│  EventHandler    │  Event processing
│                  │
│  - callback()    │  Actual event processing logic
│  - context       │  Handler context
└──────────────────┘
```

## Key Components

### 1. EventProducer

Component that publishes events to the message queue.

**Key Features:**
- Publish event objects to message queue
- Support Broadcast and Anycast event types
- Event serialization and metadata management

### 2. EventDispatcher

Component that consumes events from the message queue and routes them to registered handlers.

**Key Features:**
- Anycast event consumption (Consumer): Only one subscriber processes
- Broadcast event subscription (Subscriber): All subscribed servers can process messages
- Event handler registration and management

**Anycast vs Broadcast:**

| Type | Anycast (Consumer) | Broadcast (Subscriber) |
|------|-------------------|----------------------|
| Processing | One of all subscribers processes | All subscribed servers can process |
| Use Cases | Task distribution, load balancing | Notifications, state synchronization |
| Message Queue | Uses Consumer Group | Independent stream per subscriber |

### 3. EventHandler

Component representing registered event handlers. Handlers process specific event types and operate in Anycast (CONSUMER) or Broadcast (SUBSCRIBER) mode.

## Event Types

### Event Type Directory Structure

```
event_types/
├── kernel/          # Kernel lifecycle events
├── session/         # Session lifecycle events
├── bgtask/          # Background task events
├── agent/           # Agent events
├── vfolder/         # Virtual folder events
├── volume/          # Volume events
├── image/           # Image events
├── schedule/        # Scheduling events
├── artifact/        # Artifact events
├── artifact_registry/ # Artifact registry events
├── model_serving/   # Model serving events
├── log/             # Log events
└── idle/            # Idle status check events
```

### Major Event Types

#### Kernel Events
- `KernelTerminatedBroadcastEvent`: Kernel termination notification
- `KernelStartedBroadcastEvent`: Kernel start notification
- `KernelPullingBroadcastEvent`: Image download progress

#### Session Events
- `SessionStartedBroadcastEvent`: Session start
- `SessionTerminatedBroadcastEvent`: Session termination

#### Background Task Events
- `BgtaskUpdatedEvent`: Task progress update
- `BgtaskDoneEvent`: Task completion
- `BgtaskFailedEvent`: Task failure
- `BgtaskCancelledEvent`: Task cancellation

#### Agent Events
- `AgentHeartbeatEvent`: Agent heartbeat
- `AgentStatusChangedEvent`: Agent status change

## Component Usage Examples

**Manager**: Publishes kernel/session state change events, subscribes to agent heartbeats

**Agent**: Publishes kernel state events, subscribes to session execution requests

**Storage Proxy**: Subscribes to folder deletion events and performs cleanup tasks

## Message Queue Integration

Event Dispatcher is currently implemented based on Redis Streams.

- **Anycast**: Uses Consumer Group so only one consumer processes
- **Broadcast**: Each subscriber consumes from independent stream

## Monitoring

System status can be monitored by automatically collecting event processing success/failure metrics and processing times.

## Error Handling

### When Handler Raises Exception

- **Broadcast Events**: Continue processing without affecting other handlers
- **Anycast Events**: Message moves to reprocessing queue (retry possible)

### Retry Strategy

Automatic retry is configured at message queue level:
- Dead Letter Queue (DLQ) support
- Maximum retry count setting
- Backoff strategy

## Performance Considerations

### Handler Performance

- **Async Processing**: All handlers written as async functions
- **Avoid Blocking Operations**: CPU-intensive tasks separated into separate threads/processes
- **Lightweight Handlers**: Keep handlers lightweight and delegate heavy tasks to Background Tasks

## Related Documentation

- [Background Task System](../bgtask/README.md) - Long-running task processing
- [Message Queue](../message_queue/) - Message queue interface and implementation
- [Manager Events API](../../manager/api/events.py) - SSE-based event streaming
