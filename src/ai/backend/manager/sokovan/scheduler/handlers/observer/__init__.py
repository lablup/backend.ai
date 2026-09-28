"""Kernel observer handlers for the Sokovan scheduler.

Observers collect data from kernels without changing their state.
Unlike handlers that perform status transitions, observers are
read-only operations for metrics, fair share calculation, etc.
"""
