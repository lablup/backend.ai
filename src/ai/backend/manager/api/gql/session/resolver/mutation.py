"""Session GraphQL mutation resolvers."""

from __future__ import annotations

import strawberry
from strawberry import Info

from ai.backend.manager.api.gql.session.inputs import (
    CheckAndTransitSessionV2StatusInputGQL,
    CommitSessionV2InputGQL,
    CompleteSessionV2CodeInputGQL,
    ConvertSessionV2ToImageInputGQL,
    CreateSessionV2ClusterInputGQL,
    CreateSessionV2FromParamsInputGQL,
    CreateSessionV2FromTemplateInputGQL,
    DestroySessionV2InputGQL,
    ExecuteInSessionV2InputGQL,
    InterruptSessionV2InputGQL,
    ModifySessionV2InputGQL,
    RenameSessionV2InputGQL,
    RestartSessionV2InputGQL,
    ShutdownSessionV2ServiceInputGQL,
    StartSessionV2ServiceInputGQL,
)
from ai.backend.manager.api.gql.session.payloads import (
    CheckAndTransitSessionV2StatusPayloadGQL,
    CommitSessionV2PayloadGQL,
    CompleteSessionV2CodePayloadGQL,
    ConvertSessionV2ToImagePayloadGQL,
    CreateSessionV2PayloadGQL,
    DestroySessionV2PayloadGQL,
    ExecuteInSessionV2PayloadGQL,
    InterruptSessionV2PayloadGQL,
    ModifySessionV2PayloadGQL,
    RenameSessionV2PayloadGQL,
    RestartSessionV2PayloadGQL,
    ShutdownSessionV2ServicePayloadGQL,
    StartSessionV2ServicePayloadGQL,
)
from ai.backend.manager.api.gql.types import StrawberryGQLContext

# Modify Session


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Modify session properties such as name and priority (admin only)."
    )
)  # type: ignore[misc]
async def admin_modify_session(
    info: Info[StrawberryGQLContext],
    input: ModifySessionV2InputGQL,
) -> ModifySessionV2PayloadGQL:
    raise NotImplementedError("admin_modify_session is not yet implemented")


# Check and Transit Status


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Check the actual status of sessions and "
        "transition them to the appropriate status if needed."
    )
)  # type: ignore[misc]
async def check_and_transit_session_status(
    info: Info[StrawberryGQLContext],
    input: CheckAndTransitSessionV2StatusInputGQL,
) -> CheckAndTransitSessionV2StatusPayloadGQL:
    raise NotImplementedError("check_and_transit_session_status is not yet implemented")


# Destroy Session


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Terminate and destroy a session. "
        "Supports forced termination and recursive deletion of dependent sessions."
    )
)  # type: ignore[misc]
async def destroy_session(
    info: Info[StrawberryGQLContext],
    input: DestroySessionV2InputGQL,
) -> DestroySessionV2PayloadGQL:
    raise NotImplementedError("destroy_session is not yet implemented")


# Restart Session


@strawberry.mutation(description="Added in 26.3.0. Restart a running or terminated session.")  # type: ignore[misc]
async def restart_session(
    info: Info[StrawberryGQLContext],
    input: RestartSessionV2InputGQL,
) -> RestartSessionV2PayloadGQL:
    raise NotImplementedError("restart_session is not yet implemented")


# Rename Session


@strawberry.mutation(description="Added in 26.3.0. Rename an existing session.")  # type: ignore[misc]
async def rename_session(
    info: Info[StrawberryGQLContext],
    input: RenameSessionV2InputGQL,
) -> RenameSessionV2PayloadGQL:
    raise NotImplementedError("rename_session is not yet implemented")


# Interrupt Session


@strawberry.mutation(description="Added in 26.3.0. Send an interrupt signal to a running session.")  # type: ignore[misc]
async def interrupt_session(
    info: Info[StrawberryGQLContext],
    input: InterruptSessionV2InputGQL,
) -> InterruptSessionV2PayloadGQL:
    raise NotImplementedError("interrupt_session is not yet implemented")


# Execute in Session


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Execute code in a session. "
        "Supports multiple execution modes: query, batch, input, and continue."
    )
)  # type: ignore[misc]
async def execute_in_session(
    info: Info[StrawberryGQLContext],
    input: ExecuteInSessionV2InputGQL,
) -> ExecuteInSessionV2PayloadGQL:
    raise NotImplementedError("execute_in_session is not yet implemented")


# Commit Session


@strawberry.mutation(
    description="Added in 26.3.0. Commit the current session state for persistence."
)  # type: ignore[misc]
async def commit_session(
    info: Info[StrawberryGQLContext],
    input: CommitSessionV2InputGQL,
) -> CommitSessionV2PayloadGQL:
    raise NotImplementedError("commit_session is not yet implemented")


# Convert Session to Image


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Convert a session into a container image. "
        "Creates a background task for the conversion process."
    )
)  # type: ignore[misc]
async def convert_session_to_image(
    info: Info[StrawberryGQLContext],
    input: ConvertSessionV2ToImageInputGQL,
) -> ConvertSessionV2ToImagePayloadGQL:
    raise NotImplementedError("convert_session_to_image is not yet implemented")


# Start Session Service


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Start an app service within a session (e.g., Jupyter, TensorBoard, SSH)."
    )
)  # type: ignore[misc]
async def start_session_service(
    info: Info[StrawberryGQLContext],
    input: StartSessionV2ServiceInputGQL,
) -> StartSessionV2ServicePayloadGQL:
    raise NotImplementedError("start_session_service is not yet implemented")


# Shutdown Session Service


@strawberry.mutation(
    description="Added in 26.3.0. Shut down an app service running within a session."
)  # type: ignore[misc]
async def shutdown_session_service(
    info: Info[StrawberryGQLContext],
    input: ShutdownSessionV2ServiceInputGQL,
) -> ShutdownSessionV2ServicePayloadGQL:
    raise NotImplementedError("shutdown_session_service is not yet implemented")


# Complete Session Code


@strawberry.mutation(description="Added in 26.3.0. Request code auto-completion in a session.")  # type: ignore[misc]
async def complete_session_code(
    info: Info[StrawberryGQLContext],
    input: CompleteSessionV2CodeInputGQL,
) -> CompleteSessionV2CodePayloadGQL:
    raise NotImplementedError("complete_session_code is not yet implemented")


# Create Session from Params


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Create a new session with explicit parameters. "
        "Specifies the image, resources, and configuration directly."
    )
)  # type: ignore[misc]
async def create_session_from_params(
    info: Info[StrawberryGQLContext],
    input: CreateSessionV2FromParamsInputGQL,
) -> CreateSessionV2PayloadGQL:
    raise NotImplementedError("create_session_from_params is not yet implemented")


# Create Session from Template


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Create a new session from a predefined template. "
        "Template values can be overridden with provided fields."
    )
)  # type: ignore[misc]
async def create_session_from_template(
    info: Info[StrawberryGQLContext],
    input: CreateSessionV2FromTemplateInputGQL,
) -> CreateSessionV2PayloadGQL:
    raise NotImplementedError("create_session_from_template is not yet implemented")


# Create Session Cluster


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Create a cluster session with multiple nodes based on a template."
    )
)  # type: ignore[misc]
async def create_session_cluster(
    info: Info[StrawberryGQLContext],
    input: CreateSessionV2ClusterInputGQL,
) -> CreateSessionV2PayloadGQL:
    raise NotImplementedError("create_session_cluster is not yet implemented")
