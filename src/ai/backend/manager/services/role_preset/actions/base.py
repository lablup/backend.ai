from abc import ABC, abstractmethod


class RoleNameTemplateCarrier(ABC):
    """Declares that an action carries a preset's ``role_name_template``.

    The template is rejected at the action layer rather than inside the write, so
    a malformed one is refused before a transaction opens and the refusal is
    recorded like any other denial.
    """

    @abstractmethod
    def role_name_template(self) -> str | None:
        """The template to validate, or ``None`` when the action leaves it alone."""
        raise NotImplementedError
