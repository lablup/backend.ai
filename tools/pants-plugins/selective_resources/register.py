from __future__ import annotations

import logging

from pants.engine.addresses import Addresses, UnparsedAddressInputs
from pants.core.target_types import GenericTarget
from pants.engine.platform import Platform
from pants.engine.rules import (
    Get,
    SubsystemRule,
    collect_rules,
    rule,
)
from pants.engine.target import (
    DictStringToStringField,
    Dependencies,
    InjectedDependencies,
    InjectDependenciesRequest,
    StringField,
)
from pants.engine.unions import UnionRule
from pants.option.option_types import EnumOption
from pants.option.subsystem import Subsystem

logger = logging.getLogger(__name__)


class SelectiveResourcesSubsystem(Subsystem):
    options_scope = "selective-resources"
    help = "The selective resource source provider."
    platform = EnumOption(
        "--platform",
        default=Platform.linux_x86_64,
        enum_type=Platform,
        advanced=False,
        help="Select only resources compatible with the given platform",
    )


class PlatformSelectionField(StringField):
    alias = "platform"
    help = "Selectively inject dependencies depending on the designated platform configuration"
    default = None


class PlatformSpecificDependenciesField(Dependencies):
    alias = "platform_dependencies"
    help = "Platform-specific dependencies"


# class PlatformSpecificDependenciesField(DictStringToStringField):
#     alias = "platforms"
#     help = "Selectively inject dependencies depending on the designated platform configuration"
#     default = None


class InjectPlatformSpecificDependenciesRequest(InjectDependenciesRequest):
    inject_for = PlatformSpecificDependenciesField


@rule
async def inject_platform_specific_dependencies(
    request: InjectPlatformSpecificDependenciesRequest,
    subsystem: SelectiveResourcesSubsystem,
) -> InjectedDependencies:
    logger.info("---- request: %r", request)
    logger.info("---- selected platform: %r", subsystem.platform)
    logger.info("---- target platform: %r", request.platform)

    if request.platfrom is None or subsystem.platform != request.platform:
        return InjectedDependencies()

    unparsed_addresses = request.dependencies_field
    parsed_addresses = set(
        await Get(
            Addresses,
            UnparsedAddressInputs(
                unparsed_addresses,
                owning_address=request.address,
            ),
        )
    )
    return InjectedDependencies(Addresses(parsed_addresses))


# Plugin registration

def rules():
    return [
        *collect_rules(),
        SubsystemRule(SelectiveResourcesSubsystem),
        # GenericTarget.register_plugin_field(PlatformSpecificDependenciesField),
        GenericTarget.register_plugin_field(PlatformSelectionField),
        GenericTarget.register_plugin_field(PlatformSpecificDependenciesField),
        UnionRule(InjectDependenciesRequest, InjectPlatformSpecificDependenciesRequest),
    ]
