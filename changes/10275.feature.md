Integrate pyinfra deployment framework from backend.ai-installer into the unified install package, enabling production deployment via PyInfra alongside existing Docker-based development setup.

Key additions:
- PyInfra framework (runner, configs, os_packages) with enterprise config schemas (enabled=False in OSS)
- OSS deploy scripts (os, halfstack, cores, monitor) - 318 files, 82K+ lines
- TUI PACKAGE mode now offers choice: Release Package (existing) or Production Deployment (PyInfra)
- Horizontal card layout with keyboard navigation for deployment type selection
