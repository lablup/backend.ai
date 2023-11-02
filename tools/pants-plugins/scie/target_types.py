# Copyright 2022 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from enum import Enum

from pants.core.goals.package import OutputPathField
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    Dependencies,
    DictStringToStringField,
    NestedDictStringToStringField,
    OptionalSingleSourceField,
    StringSequenceField,
    Target,
)
from pants.util.strutil import softwrap


class ScieDependenciesField(Dependencies):
    required = True
    supports_transitive_excludes = True
    help = softwrap(
        """
        The address of a single `pex_binary` target to include in the binary, e.g.
        `['src/python/project:pex']`.
        """
    )


class ScieBinaryNameField(OutputPathField):
    alias = "binary_name"
    default = None
    help = softwrap(
        """
        The name of the binary that will be output by `scie-jump`. If not set, this will default
        to the name of this target.
        """
    )


class SciePlatform(Enum):
    LINUX_AARCH64 = "linux-aarch64"
    LINUX_X86_64 = "linux-x86_64"
    MACOS_AARCH64 = "macos-aarch64"
    MACOS_X86_64 = "macos-x86_64"


class SciePlatformField(StringSequenceField):
    alias = "platforms"
    default = None
    valid_choices = SciePlatform
    help = softwrap(
        """
        A field to indicate what what platform(s) to build for.

        The default selection is `None`, in which case we will default to the current platform.
        Possible values are: `linux-aarch64`, `linux-x86_64`, `macos-aarch64`, `macos-x86_64`.
        """
    )


class ScieLiftSourceField(OptionalSingleSourceField):
    alias = "lift"
    expected_file_extensions = (".toml",)
    default = None
    help = softwrap(
        """
        If set, the specified toml file will be used to configure the `scie` and all other
        fields will be ignored.

        The path is relative to the BUILD file's directory and it must end in a `.toml` extension.

        Example:
            lift = "helloworldlift.toml"

        Inside the toml, strings that are prefixed with `:` will be interpreted as references to
        other targets. For example, `:mypex` will be interpreted as a reference to the
        `mypex` target in the same BUILD file and the Lift file will be updated to include
        the `mypex` location.

        Example:
        [[lift.files]]
            name = ":helloworld-pex"
        """
    )


# class ScieCommandField(NestedDictStringToStringField):
#     alias = "commands"
#     default = None
#     help = softwrap(
#         """
#         A field to indicate what command to run when the binary is executed.

#         The default selection is `None`, in which case we will call the bundled PEX
#         file using the Python interpreter: e.g. `python my_binary.pex`.

#         If you want to allow for different command(s) you can specify them here. If you
#         want a default command, you can specify it with an empty name ("") as the key.

#         This field is passed straight-through to the `science` command without any
#         modification.

#         Example:
#         commands = {
#             "": {
#                 "exe": "#{cpython:python}"

#                 "description": "My default command",
#                 "env": {

#             }
#             "run": "python my_binary.pex",


#         Refer to https://github.com/a-scie/jump/blob/main/docs/packaging.md for more
#         information on the available boot.command options.
#         """
#     )


class ScieTarget(Target):
    alias = "scie_binary"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        ScieDependenciesField,
        ScieBinaryNameField,
        SciePlatformField,
        ScieLiftSourceField,
    )
    help = softwrap(
        """
        A single-file Python executable with a Python interpreter embedded, built via scie-jump.

        To use this target, first create a `pex_binary` target with the code you want included
        in your binary, per {doc_url('pex-files')}. Then add this `pex_binary` target to the
        `dependencies` field. See the `help` for `dependencies` for more information.
        """
    )
