from __future__ import annotations

import logging
from dataclasses import dataclass

from pants.engine.addresses import Addresses, UnparsedAddressInputs
from pants.engine.platform import Platform
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    Dependencies,
    DictStringToStringField,
    FieldSet,
    InferDependenciesRequest,
    InferredDependencies,
    Target,
)
from pants.engine.unions import UnionRule
from pants.option.option_types import EnumOption
from pants.option.subsystem import Subsystem

logger = logging.getLogger(__name__)


class PlatformResourcesSubsystem(Subsystem):
    options_scope = "platform-specific-resources"
    help = "The platform-specific resource provider."
    platform = EnumOption(
        "--target",
        default=lambda cls: Platform.create_for_localhost(),
        enum_type=Platform,
        advanced=False,
        help="Select only resources compatible with the given platform",
    )


class PlatformDependencyMapField(DictStringToStringField):
    alias = "dependency_map"
    help = (
        "Specifies platform-specific dependencies as a dictionary from platform names to dependency"
        " lists."
    )


class PlatformSpecificDependenciesField(Dependencies):
    """
    This field will be populated by injection based on the `--platform-specific-resources-target` option
    and from the `dependency_map` field of the `platform_resources` target.
    """


class PlatformResourcesTarget(Target):
    alias = "platform_resources"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        PlatformDependencyMapField,
        PlatformSpecificDependenciesField,
    )
    help = "A target to declare selective dependency sets for multiple different platforms"


@dataclass(frozen=True)
class PlatformSpecificDependencyInferenceFieldSet(FieldSet):
    required_fields = (
        PlatformSpecificDependenciesField,
        PlatformDependencyMapField,
    )
    dependencies: PlatformSpecificDependenciesField
    dependency_map: PlatformDependencyMapField


class InferPlatformSpecificDependenciesRequest(InferDependenciesRequest):
    infer_from = PlatformSpecificDependencyInferenceFieldSet


@rule
async def infer_platform_specific_dependencies(
    request: InferPlatformSpecificDependenciesRequest,
    subsystem: PlatformResourcesSubsystem,
) -> InferredDependencies:
    logger.info("infer_platform_specific_dependencies")
    logger.info(
        "configured target platform (%s) = %s",
        request.field_set.address,
        subsystem.platform.value,
    )
    platform_resources_unparsed_address = request.field_set.dependency_map.value.get(
        subsystem.platform.value
    )
    if not platform_resources_unparsed_address:
        return InferredDependencies(Addresses([]))
    parsed_addresses = await Get(
        Addresses,
        UnparsedAddressInputs(
            (platform_resources_unparsed_address,),
            owning_address=request.field_set.address,
            description_of_origin="platform_resources",
        ),
    )
    return InferredDependencies(Addresses(parsed_addresses))


# Plugin registration


def target_types():
    return (PlatformResourcesTarget,)


def rules():
    return [
        *collect_rules(),
        *PlatformResourcesSubsystem.rules(),
        UnionRule(InferDependenciesRequest, InferPlatformSpecificDependenciesRequest),
    ]
