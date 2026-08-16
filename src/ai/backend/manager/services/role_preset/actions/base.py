from abc import ABC, abstractmethod


class RoleNameTemplateCarrier(ABC):
    """Declares that an action carries a preset's ``role_name_template``.

    Rejected at the action layer rather than inside the write, so a malformed template
    is refused before a transaction opens.
    """

    @abstractmethod
    def role_name_template(self) -> str | None:
        """The template to validate, or ``None`` when the action leaves it alone."""
        raise NotImplementedError
