# Enterprise Deployment Scripts

This directory is reserved for enterprise-only deployment scripts.

## Enterprise Features

The following deployment modules require `backend.ai-installer` (enterprise):
- **FastTrack**: Workflow engine
- **License Server**: License management
- **Control Panel**: Admin control panel
- **Graylog**: Log aggregation (alternative to Loki)
- **Zabbix**: Infrastructure monitoring (alternative to Prometheus)

## OSS vs Enterprise

**Backend.AI OSS** provides:
- Core services (Manager, Agent, WebServer, StorageProxy, AppProxy)
- Halfstack (PostgreSQL, Redis, Etcd)
- Monitoring (Prometheus, Grafana, Loki)
- Configuration schemas for enterprise features (enabled=False)

**Backend.AI Enterprise** adds:
- Actual deployment scripts for enterprise features
- Production-ready HA configurations
- Advanced monitoring and logging
- Enterprise support

## Usage

For enterprise deployments, see `backend.ai-installer` repository.
