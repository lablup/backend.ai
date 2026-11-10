"""Tracker filters applied before agent selection.

- exclusion: drops agents no state change can save (architecture, strict
  designation)
- stateful: drops agents whose current resource state falls short (slots,
  container cap) — these can pass again once resources are reclaimed
"""
