"""AppConfigFragment GraphQL API package.

Resolver and type names are re-exported by ``schema.py`` directly via
their submodules to keep this package's ``__init__`` import-light: a
top-level ``from app_config_fragment import ...`` would otherwise drag
in the mutation resolvers, which back-import from
``app_config.types.bulk_payloads`` and form an import cycle when
``AppConfigGQL`` is loading.
"""
