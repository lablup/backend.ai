"""Variable interpolation for service commands and pre-start action args.

The syntax is chosen per service start from ``ModelServiceConfig.interpolation`` or the
app's start options; ``registry.INTERPOLATORS`` maps each mode to its implementation.
"""
