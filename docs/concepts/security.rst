.. _concept-security:

Security Architecture
=====================

This section describes the security architecture and assumptions of Backend.AI,
focusing on network isolation requirements for production deployments.

.. warning::

   **Critical Security Requirement: Network Isolation**

   Backend.AI assumes compute nodes (where Agents run) are deployed in a
   network-isolated environment with restricted inbound access. Direct access
   to compute nodes from untrusted networks must be prevented through proper
   network configuration.


Network Architecture Overview
------------------------------

Backend.AI follows a defense-in-depth approach where different components are
deployed in isolated network zones with controlled access paths.

Architecture Diagram
^^^^^^^^^^^^^^^^^^^^

The following diagram illustrates the expected network architecture and traffic
flow in a properly configured Backend.AI cluster:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                     Public Network                          │
   │                  (Untrusted Network)                        │
   └──────────────────────────┬──────────────────────────────────┘
                              │
                              │ HTTPS (443)
                              │
                        ┌─────▼─────┐
                        │  Firewall  │
                        │   / WAF    │
                        └─────┬─────┘
                              │
   ┌──────────────────────────┼──────────────────────────────────┐
   │                          │      Management Zone             │
   │                    ┌─────▼─────┐                           │
   │                    │ Webserver │ ◄─── Web UI / REST API    │
   │                    └─────┬─────┘                           │
   │                          │                                  │
   │                    ┌─────▼─────┐                           │
   │                    │  Manager  │ ◄─── Business Logic       │
   │                    └─────┬─────┘                           │
   │                          │                                  │
   │                    ┌─────▼─────┐                           │
   │                    │ AppProxy  │ ◄─── Interactive Sessions │
   │                    └─────┬─────┘                           │
   │                          │                                  │
   └──────────────────────────┼──────────────────────────────────┘
                              │
                              │ Internal Network Only
                              │ (No Direct Public Access)
                              │
   ┌──────────────────────────┼──────────────────────────────────┐
   │                          │      Compute Zone                │
   │                          │   (Private Network)              │
   │                    ┌─────▼─────┐                           │
   │           ┌────────┤   Agent   ├────────┐                  │
   │           │        └───────────┘        │                  │
   │     ┌─────▼─────┐              ┌────────▼──────┐          │
   │     │ Container │              │   Container    │          │
   │     │ (Session) │              │   (Session)    │          │
   │     └───────────┘              └────────────────┘          │
   │                                                             │
   └─────────────────────────────────────────────────────────────┘

Traffic Flow
^^^^^^^^^^^^

**Authorized Access Path:**

1. **User → Webserver**: Users connect to the webserver via HTTPS through a
   firewall or Web Application Firewall (WAF)

2. **Webserver → Manager**: Webserver forwards authenticated requests to the
   manager for processing

3. **Manager → Agent**: Manager communicates with agents in the compute zone
   via internal network for session lifecycle management

4. **User → AppProxy → Agent → Container**: For interactive sessions (notebooks,
   terminals, web apps), users connect through AppProxy which proxies traffic
   to containers running on agents

**Blocked Access Path:**

* **User → Agent**: Direct access from public network to agents must be blocked
* **User → Container**: Direct access from public network to containers must be blocked

Network Zones
-------------

Management Zone
^^^^^^^^^^^^^^^

The management zone contains Backend.AI control plane components:

* **Webserver**: Web UI and REST API gateway
* **Manager**: Core business logic and orchestration
* **AppProxy**: Interactive session proxy
* **Database**: PostgreSQL for persistent state
* **Etcd**: Configuration and coordination
* **Redis**: Caching and pub/sub

**Network Requirements:**

* Must be accessible from trusted networks (VPN, corporate network)
* Should be protected by firewall rules allowing only necessary ports
* Should implement rate limiting and DDoS protection
* TLS/SSL encryption must be enabled for all external-facing services

Compute Zone
^^^^^^^^^^^^

The compute zone contains Backend.AI data plane components:

* **Agents**: Container orchestration and resource management
* **Containers**: User computation workloads

**Network Requirements:**

* **CRITICAL**: Must be isolated in a private network with NO direct inbound
  access from untrusted networks
* Agents must be able to initiate connections to management zone components
* Containers should only be accessible via AppProxy tunnel
* Inter-agent communication required for multi-node cluster sessions via
  overlay networks

Security Considerations
-----------------------

Interactive Session Access Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Issue**: Interactive sessions do not verify authorization when accessed directly

**Impact**: If compute nodes are accessible from untrusted networks, attackers
could potentially access running sessions by bypassing the authentication layer

**Mitigation**: By design, Backend.AI assumes compute nodes are deployed in a
network-isolated environment. This is not a software vulnerability but an
operational security requirement that must be enforced through proper network
configuration.


References
----------

* :doc:`../install/index` - Backend.AI Installation Guide
* :doc:`networking` - Networking Concepts
* :doc:`../install/install-from-package/install-agent` - Agent Installation
