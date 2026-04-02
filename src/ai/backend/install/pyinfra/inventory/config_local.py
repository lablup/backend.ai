"""
Pyinfra config for local dev deployment.

Disables sudo (not needed for local @local connector where we own everything).
Loaded by pyinfra when placed alongside the inventory file, or via --config flag.
"""

# Disable sudo globally — local dev runs as current user
SUDO = False
USE_SUDO_LOGIN = False
