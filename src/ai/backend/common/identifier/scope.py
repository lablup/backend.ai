import uuid

__all__ = ("ScopeID",)


# A scope's identifier. Polymorphic across scope kinds (domain/project/user/...);
# the concrete kind is discriminated by the accompanying scope_type, so this is
# a transparent alias for uuid.UUID rather than a distinct NewType.
type ScopeID = uuid.UUID
