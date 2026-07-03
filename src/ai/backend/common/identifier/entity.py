import uuid

__all__ = ("EntityID",)


# An entity's identifier. Polymorphic across entity kinds (session/kernel/vfolder/...);
# the concrete kind is discriminated by the accompanying entity_type, so this is
# a transparent alias for uuid.UUID rather than a distinct NewType.
type EntityID = uuid.UUID
