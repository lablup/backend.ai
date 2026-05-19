"""Pluggable network providers for the containerd backend.

``base`` defines the ``NetworkProvider`` abstraction; ``cni`` and ``netns``
are the shared, provider-agnostic CNI/netns machinery every provider uses.
"""
