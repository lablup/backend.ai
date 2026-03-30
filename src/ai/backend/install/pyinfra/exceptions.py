"""
Backend.AI PyInfra Deployment Exceptions

Custom exception classes for Backend.AI deployment operations.
These exceptions provide clear error handling across all deployment scripts.
"""


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid.

    This exception is used when:
    - Required configuration sections are missing from host_data.services
    - Critical configuration values are None, empty, or invalid
    - Configuration validation fails during deployment initialization

    Examples:
        raise ConfigurationError("Missing required configuration: postgres.hostname")
        raise ConfigurationError("bai_core.version is required but not set")
    """

    pass


class DeploymentError(Exception):
    """Raised when deployment operations fail.

    This exception is used when:
    - Package installation fails
    - File operations fail (templates, directories, etc.)
    - Service management operations fail
    - Any critical deployment step encounters an error

    Examples:
        raise DeploymentError("Failed to install backend.ai-manager: pip error")
        raise DeploymentError("Template rendering failed: missing variable")
    """

    pass


class ValidationError(Exception):
    """Raised when validation checks fail.

    This exception is used when:
    - Pre-deployment validation fails
    - Post-deployment verification fails
    - Service health checks fail

    Examples:
        raise ValidationError("Service is not running after installation")
        raise ValidationError("Configuration file validation failed")
    """

    pass


class ServiceError(Exception):
    """Raised when service-specific operations fail.

    This exception is used when:
    - Systemd service operations fail
    - Service-specific configuration errors
    - Service dependency issues

    Examples:
        raise ServiceError("Failed to start systemd service: backendai-manager")
        raise ServiceError("Service dependency not available: postgres")
    """

    pass


class MissingAttributeError(DeploymentError):
    """Raised when required attribute is not set in deployment class.

    This exception is used when:
    - Required instance attributes are None or not set
    - Subclass __init__ doesn't initialize mandatory attributes
    - Method parameters require fallback to instance attributes that don't exist

    Examples:
        raise MissingAttributeError("service_name", "ManagerDeploy")
        raise MissingAttributeError("python_venv_path", self.__class__.__name__)
    """

    def __init__(self, attr_name: str, class_name: str) -> None:
        self.attr_name = attr_name
        self.class_name = class_name
        super().__init__(
            f"'{attr_name}' must be set in {class_name}.__init__.\nExample: self.{attr_name} = ..."
        )


class TemplateNotFoundError(DeploymentError):
    """Raised when template file is not found in expected locations.

    This exception is used when:
    - Template file doesn't exist in any searched paths
    - Template discovery fails in hierarchical search
    - Template name is incorrect or file is missing

    Examples:
        raise TemplateNotFoundError("config.toml.j2", ["/path/1", "/path/2"])
        raise TemplateNotFoundError(str(template_path), searched_locations)
    """

    def __init__(self, template_name: str, searched_paths: list[str]) -> None:
        self.template_name = template_name
        self.searched_paths = searched_paths
        paths_str = "\n  - ".join(searched_paths)
        super().__init__(f"Template '{template_name}' not found.\nSearched in:\n  - {paths_str}")


class ServiceStateError(DeploymentError):
    """Raised when service is in unexpected state.

    This exception is used when:
    - Service should be running but is stopped
    - Service should be stopped but is running
    - Service state transitions fail
    - Health checks indicate unexpected service state

    Examples:
        raise ServiceStateError("Service is not running after installation")
        raise ServiceStateError("Cannot update running service, stop it first")
    """

    pass
