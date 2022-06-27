from __future__ import annotations

import logging

from pants.engine.addresses import Address, Addresses, UnparsedAddressInputs
from pants.engine.platform import Platform
from pants.engine.rules import Get, SubsystemRule, collect_rules, rule
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    Dependencies,
    DictStringToStringField,
    InjectDependenciesRequest,
    InjectedDependencies,
    Target,
    WrappedTarget,
)
from pants.engine.unions import UnionRule
from pants.option.option_types import EnumOption
from pants.option.subsystem import Subsystem

logger = logging.getLogger(__name__)


class PlatformResourcesSusbystem(Subsystem):
    options_scope = "platform-specific-resources"
    help = "The platform-specific resource provider."
    platform = EnumOption(
        "--target",
        default=Platform.current,
        enum_type=Platform,
        advanced=False,
        help="Select only resources compatible with the given platform",
    )


class PlatformDependencyMapField(DictStringToStringField):
    alias = "dependency_map"
    help = "Specifies platform-specific dependencies as a dictionary from platform names to dependency lists."


class PlatformSpecificDependencies(Dependencies):
    """
    This field will be populated by injection based on the `--platform-specific-resources-target` option
    and from the `dependency_map` field of the `platform_resources` target.
    """


class PlatformResourcesTarget(Target):
    alias = "platform_resources"
    core_fields = (*COMMON_TARGET_FIELDS, PlatformDependencyMapField, PlatformSpecificDependencies)
    help = "A target to declare selective dependency sets for multiple different platforms"


class InjectPlatformSpecificDependenciesRequest(InjectDependenciesRequest):
    inject_for = PlatformSpecificDependencies


@rule
async def inject_platform_specific_dependencies(
    request: InjectPlatformSpecificDependenciesRequest,
    subsystem: PlatformResourcesSusbystem,
) -> InjectedDependencies:
    logger.info(
        "configured target platform (%s) = %s",
        request.dependencies_field.address,
        subsystem.platform.value,
    )
    wrapped_target = await Get(WrappedTarget, Address, request.dependencies_field.address)
    platforms = wrapped_target.target.get(PlatformDependencyMapField).value
    platform_resources_unparsed_address = platforms and platforms.get(subsystem.platform.value)
    if not platform_resources_unparsed_address:
        return InjectedDependencies()
    parsed_addresses = await Get(
        Addresses,
        UnparsedAddressInputs(
            (platform_resources_unparsed_address,),
            owning_address=request.dependencies_field.address,
        ),
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
        SubsystemRule(PlatformResourcesSusbystem),
        UnionRule(InjectDependenciesRequest, InjectPlatformSpecificDependenciesRequest),
    ]
