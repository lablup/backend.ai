from __future__ import annotations

import logging

from pants.engine.addresses import Address, Addresses, UnparsedAddressInputs
from pants.core.target_types import GenericTarget
from pants.engine.platform import Platform
from pants.engine.rules import (
    Get,
    SubsystemRule,
    collect_rules,
    rule,
)
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    DictStringToStringField,
    Dependencies,
    InjectedDependencies,
    InjectDependenciesRequest,
    StringField,
    Target,
    WrappedTarget,
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


# class PlatformSelectionField(StringField):
#     alias = "platform"
#     help = "Selectively inject dependencies depending on the designated platform configuration"
#     default = None


# class PlatformSpecificDependenciesField(Dependencies):
#     alias = "platform_dependencies"
#     help = "Platform-specific dependencies"


class PlatformsField(DictStringToStringField):
    alias = "platforms"
    help = "Selectively inject dependencies depending on the designated platform configuration"


class PlatformSpecificDependenciesField(Dependencies):
    """This field will be populated by injection based on the `--selective-resources-platform` from the
    `platforms` field of the `platform_resources` target.

    """


class PlatformResourcesTarget(Target):
    alias = "platform_resources"
    core_fields = (*COMMON_TARGET_FIELDS, PlatformsField, PlatformSpecificDependenciesField)


class InjectPlatformSpecificDependenciesRequest(InjectDependenciesRequest):
    inject_for = PlatformSpecificDependenciesField


@rule
async def inject_platform_specific_dependencies(
    request: InjectPlatformSpecificDependenciesRequest,
    subsystem: SelectiveResourcesSubsystem,
) -> InjectedDependencies:
    logger.info("---- request: %r", request)
    logger.info("---- selected platform: %r", subsystem.platform)
    # logger.info("---- target platform: %r", request.platform)

    wrapped_target = await Get(WrappedTarget, Address, request.dependencies_field.address)
    platforms = wrapped_target.target.get(PlatformsField).value

    logger.info(f"=== Platforms: {platforms}\n")

    platform_resources_unparsed_address = platforms and platforms.get(subsystem.platform.value)
    if not platform_resources_unparsed_address:
        return InjectedDependencies()

    parsed_addresses = await Get(
        Addresses,
        UnparsedAddressInputs(
            (platform_resources_unparsed_address,),
            owning_address=request.dependencies_field.address,
        )
    )
    return InjectedDependencies(Addresses(parsed_addresses))


# Plugin registration


def target_types():
    return (
        PlatformResourcesTarget,
    )


def rules():
    return [
        *collect_rules(),
        SubsystemRule(SelectiveResourcesSubsystem),
        # GenericTarget.register_plugin_field(PlatformSpecificDependenciesField),
        # GenericTarget.register_plugin_field(PlatformSelectionField),
        # GenericTarget.register_plugin_field(PlatformSpecificDependenciesField),
        UnionRule(InjectDependenciesRequest, InjectPlatformSpecificDependenciesRequest),
    ]
