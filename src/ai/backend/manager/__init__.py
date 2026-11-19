with open(__file__.removesuffix("__init__.py") + "VERSION") as _version_file:
    __version__ = _version_file.read().strip()
del _version_file
