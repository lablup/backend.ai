# Event Types & Registration Flow Details

> Parent document: [BEP-1046](../BEP-1046-unified-service-discovery.md)

## Event Type Definitions

SD events are defined using the existing Redis Stream event infrastructure.

```python
# src/ai/backend/common/events/event_types/service_discovery/anycast.py

class ServiceEndpointInfo(BaseModel):
    role: str
    scope: str
    address: str
    port: int
    protocol: str
    metadata: dict[str, str] = Field(default_factory=dict)

class ServiceRegisteredEvent(AbstractAnycastEvent):
    """Service registration and heartbeat event (upsert semantics)"""
    instance_id: str        # Upsert by (service_group, instance_id)
    service_group: str
    display_name: str
    version: str
    labels: dict[str, str]
    endpoints: list[ServiceEndpointInfo]
    startup_time: datetime  # Service process start time
    config_hash: str        # Hash for config change detection

class ServiceDeregisteredEvent(AbstractAnycastEvent):
    """Service deregistration event"""
    instance_id: str
    service_group: str
```

- **Anycast**: Only one Manager instance in the consumer group processes each event
- Add `SERVICE_DISCOVERY = "service_discovery"` to existing `EventDomain`
- Uses Redis Stream `"events"` (DB 4) — same channel as existing events

## Registration Flow Details

```
[Startup]
Each component server starts
  ↓
Read [service-discovery] config + compute config_hash
  ↓
Publish ServiceRegisteredEvent (anycast via Redis Stream)
  ↓
Manager EventDispatcher consumes
  ↓
UPSERT service_catalog + service_catalog_endpoint (DB)

[Heartbeat]
Re-publish ServiceRegisteredEvent every 60 seconds
  → Manager compares config_hash:
    - Changed: full UPSERT of service_catalog + endpoints
    - Unchanged: update last_heartbeat only (lightweight update)

[Shutdown]
Publish ServiceDeregisteredEvent on graceful shutdown
  → Manager sets status = DEREGISTERED

[Stale Detection]
Manager background sweep (every 5 minutes)
  → Mark status = UNHEALTHY when last_heartbeat > 5 minutes old
```

## config_hash Optimization

`config_hash` is a hash of the entire `[service-discovery]` config. During heartbeat, it's compared with the previous hash — if unchanged, only the `last_heartbeat` timestamp is updated. This minimizes DB load.

## Per-Component Event Publishing Capability

| Component | EventProducer | Redis Stream | Changes Required |
|-----------|:---:|:---:|:---:|
| Manager | O | O | Add self-registration |
| Agent | O | O | Add SD event publishing |
| Storage Proxy | O | O | Add SD event publishing |
| AppProxy Coordinator | O | O | Add SD event publishing |
| AppProxy Worker | O | O | Add SD event publishing |
| Webserver | X | X | Add EventProducer |
