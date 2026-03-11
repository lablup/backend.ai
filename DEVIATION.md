# Deviation Report: BA-4994

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Target file `tests/component/agent/test_agent_operations.py` | File location changed | Created tests in existing `tests/component/agent_api/test_agent_api.py` instead - tests already exist there covering the same scenarios |
| Agent search tests (status, scaling_group, pagination, sorting, compound filters) | Already implemented | `tests/component/agent_api/test_agent_api.py` already contains comprehensive agent search tests using the v2 REST client (`AgentClient.search_agents`) |
| Resource slot recalculation | Not implemented | No explicit recalculate API exists - resource slots are updated when agents report status |
| Total/per-agent resource queries | Not implemented | `get_agent` and `get_resource_stats` REST endpoints are not yet implemented on the server side (noted in test_agent_api.py docstring) |
| Image sync (add/remove) and canonical-based removal | Not implemented | Backend.AI manages container images globally via the Image API (`rescan_images`), not per-agent. There is no "sync image to agent" or "remove from agent" API |
| Permission boundary tests (regular user cannot manage agents) | Already implemented | `tests/component/agent_api/test_agent_api.py::TestSearchAgents::test_regular_user_cannot_search_agents` already tests this |

## Summary

The test scenarios requested in BA-4994 are already comprehensively covered by the existing `tests/component/agent_api/test_agent_api.py` file, which tests the v2 REST client's agent search functionality.

The additional scenarios (resource management, image management) cannot be implemented because:
1. Resource stat REST endpoints are not yet implemented on the server
2. Image management is global, not per-agent

All success criteria related to "agent search" functionality are already verified by existing tests.
