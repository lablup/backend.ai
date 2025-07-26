"""
Stage-based setup system for Backend.AI Manager.

This package provides a modular, dependency-aware approach to setting up
manager components using the Stage framework.

Key components:
- stage_group.py: Main stage orchestration and dependency management
- spec_generators.py: SpecGenerator implementations for cross-stage dependencies
- usage_example.py: Examples of how to use the stage system

Benefits over monolithic SetupProvisioner:
- Clear dependency visualization and management
- Modular setup (can enable/disable specific stages)
- Concurrent setup where dependencies allow
- Type-safe dependency injection via SpecGenerators
- Easy testing and debugging of individual components
"""

from .stage_group import SetupStageGroup, create_setup_stages, setup_all_stages, teardown_all_stages

__all__ = [
    "SetupStageGroup",
    "create_setup_stages",
    "setup_all_stages",
    "teardown_all_stages",
]
