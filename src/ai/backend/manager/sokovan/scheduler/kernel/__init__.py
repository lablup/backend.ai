"""
Kernel state management module for Sokovan scheduler.

This module handles kernel lifecycle events and state transitions,
decoupled from session state management for better separation of concerns.
"""

from .state_engine import KernelStateEngine

__all__ = [
    "KernelStateEngine",
]
