"""CLI commands for notification system."""

from __future__ import annotations

import json
import sys
from typing import IO, Optional
from uuid import UUID

import click

from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session
from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)
from ai.backend.common.dto.manager.notification import (
    CreateNotificationChannelRequest,
    CreateNotificationRuleRequest,
    NotificationChannelFilter,
    NotificationRuleFilter,
    SearchNotificationChannelsRequest,
    SearchNotificationRulesRequest,
    UpdateNotificationChannelRequest,
    UpdateNotificationRuleRequest,
    ValidateNotificationChannelRequest,
)

from .extensions import pass_ctx_obj
from .notification_utils import print_notification_schema
from .pretty import print_done, print_fail
from .types import CLIContext


@click.group()
def notification():
    """Set of notification operations (channels and rules)"""


# Channel commands


@notification.group()
def channel():
    """Manage notification channels"""


@channel.command("list")
@pass_ctx_obj
@click.option("--enabled-only", is_flag=True, help="Only list enabled channels")
def list_channels_cmd(ctx: CLIContext, enabled_only: bool) -> None:
    """
    List all notification channels.
    """
    with Session() as session:
        try:
            filter_cond = None
            if enabled_only:
                filter_cond = NotificationChannelFilter(enabled=True)

            request = SearchNotificationChannelsRequest(filter=filter_cond)
            result = session.Notification.list_channels(request)

            channels = result.channels
            if not channels:
                print("No channels found")
                return
            for channel in channels:
                print(f"ID: {channel.id}")
                print(f"Name: {channel.name}")
                print(f"Type: {channel.channel_type}")
                print(f"Enabled: {channel.enabled}")
                print(f"Description: {channel.description or ''}")
                print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("info")
@pass_ctx_obj
@click.argument("channel_id", type=str)
def info_channel_cmd(ctx: CLIContext, channel_id: str) -> None:
    """
    Display detailed information of a notification channel.

    \b
    CHANNEL_ID: The channel ID
    """
    with Session() as session:
        try:
            result = session.Notification.get_channel(UUID(channel_id))
            channel = result.channel
            print(json.dumps(channel.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("create")
@pass_ctx_obj
@click.argument("name", type=str)
@click.argument("url", type=str)
@click.option("--channel-type", default="webhook", help="Channel type (default: WEBHOOK)")
@click.option("--description", type=str, default=None, help="Channel description")
@click.option("--disabled", is_flag=True, help="Create channel as disabled")
def create_channel_cmd(
    ctx: CLIContext,
    name: str,
    url: str,
    channel_type: str,
    description: Optional[str],
    disabled: bool,
) -> None:
    """
    Create a new notification channel.

    \b
    NAME: Channel name
    URL: Webhook URL
    """
    with Session() as session:
        try:
            request = CreateNotificationChannelRequest(
                name=name,
                channel_type=NotificationChannelType(channel_type),
                config=WebhookConfig(url=url),
                description=description,
                enabled=not disabled,
            )
            result = session.Notification.create_channel(request)
            channel = result.channel
            print_done(f"Channel created: {channel.id}")
            print(json.dumps(channel.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("update")
@pass_ctx_obj
@click.argument("channel_id", type=str)
@click.option("--name", type=str, default=None, help="Update channel name")
@click.option("--url", type=str, default=None, help="Update webhook URL")
@click.option("--description", type=str, default=None, help="Update channel description")
@click.option("--enable", "enabled", flag_value=True, default=None, help="Enable the channel")
@click.option("--disable", "enabled", flag_value=False, default=None, help="Disable the channel")
def update_channel_cmd(
    ctx: CLIContext,
    channel_id: str,
    name: Optional[str],
    url: Optional[str],
    description: Optional[str],
    enabled: Optional[bool],
) -> None:
    """
    Update a notification channel.

    \b
    CHANNEL_ID: The channel ID to update
    """
    with Session() as session:
        try:
            config = None
            if url:
                config = WebhookConfig(url=url)

            request = UpdateNotificationChannelRequest(
                name=name,
                description=description,
                config=config,
                enabled=enabled,
            )
            result = session.Notification.update_channel(UUID(channel_id), request)
            channel = result.channel
            print_done(f"Channel updated: {channel_id}")
            print(json.dumps(channel.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("delete")
@pass_ctx_obj
@click.argument("channel_id", type=str)
def delete_channel_cmd(ctx: CLIContext, channel_id: str) -> None:
    """
    Delete a notification channel.

    \b
    CHANNEL_ID: The channel ID to delete
    """
    with Session() as session:
        try:
            result = session.Notification.delete_channel(UUID(channel_id))
            if result.deleted:
                print_done(f"Channel deleted: {channel_id}")
            else:
                print_fail(f"Failed to delete channel: {channel_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("validate")
@pass_ctx_obj
@click.argument("channel_id", type=str)
@click.option(
    "--data",
    type=str,
    default=None,
    help="Test message to send through the channel",
)
@click.option(
    "--data-file",
    type=click.File("r"),
    default=None,
    help="Path to file containing test message (use '-' for stdin)",
)
def validate_channel_cmd(
    ctx: CLIContext,
    channel_id: str,
    data: Optional[str],
    data_file: Optional[IO],
) -> None:
    """
    Validate a notification channel by sending a test webhook.

    \b
    CHANNEL_ID: The channel ID to validate
    """
    with Session() as session:
        try:
            # Validate mutual exclusivity
            if data and data_file:
                print_fail("Cannot specify both --data and --data-file")
                sys.exit(ExitCode.FAILURE)
            if not data and not data_file:
                print_fail("Must specify either --data or --data-file")
                sys.exit(ExitCode.FAILURE)

            # Get test message content
            test_message = data_file.read() if data_file else data
            assert test_message is not None  # Type narrowing

            request = ValidateNotificationChannelRequest(test_message=test_message)
            result = session.Notification.validate_channel(UUID(channel_id), request)
            if result.success:
                print_done(f"Channel validation successful: {channel_id}")
                print(result.message)
            else:
                print_fail(f"Channel validation failed: {channel_id}")
                print(result.message)
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Rule commands


@notification.group()
def rule():
    """Manage notification rules"""


@rule.command("types")
@pass_ctx_obj
def list_rule_types_cmd(ctx: CLIContext) -> None:
    """
    List all available notification rule types with their schemas.
    """
    with Session() as session:
        try:
            result = session.Notification.list_rule_types()
            rule_types = result.rule_types
            if not rule_types:
                print("No rule types available")
                return

            print("Available notification rule types:\n")
            for rule_type in rule_types:
                print(f"• {rule_type}")
                # Fetch schema for this rule type
                try:
                    schema_result = session.Notification.get_rule_type_schema(rule_type)
                    print_notification_schema(schema_result.json_schema)
                    print()  # Empty line between rule types
                except Exception as schema_error:
                    print(f"  (Could not fetch schema: {schema_error})")
                    print()
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("schema")
@pass_ctx_obj
@click.argument("rule_type", type=str)
def rule_type_schema_cmd(ctx: CLIContext, rule_type: str) -> None:
    """
    Display schema for a notification rule type's message format.

    \\b
    RULE_TYPE: The notification rule type (e.g., session.started)
    """
    with Session() as session:
        try:
            from ai.backend.common.data.notification import NotificationRuleType

            result = session.Notification.get_rule_type_schema(NotificationRuleType(rule_type))
            print(f"Schema for rule type: {result.rule_type}\n")
            print_notification_schema(result.json_schema, indent=0)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("list")
@pass_ctx_obj
@click.option("--enabled-only", is_flag=True, help="Only list enabled rules")
@click.option(
    "--rule-types",
    type=str,
    multiple=True,
    help="Filter by rule types (can be specified multiple times)",
)
def list_rules_cmd(ctx: CLIContext, enabled_only: bool, rule_types: tuple[str, ...]) -> None:
    """
    List all notification rules.
    """
    with Session() as session:
        try:
            filter_cond = None
            if enabled_only or rule_types:
                # Convert string rule types to enum
                enum_rule_types = (
                    [NotificationRuleType(rt) for rt in rule_types] if rule_types else None
                )
                filter_cond = NotificationRuleFilter(
                    enabled=True if enabled_only else None,
                    rule_types=enum_rule_types,
                )

            request = SearchNotificationRulesRequest(filter=filter_cond)
            result = session.Notification.list_rules(request)

            rules = result.rules
            if not rules:
                print("No rules found")
                return
            for rule in rules:
                print(f"ID: {rule.id}")
                print(f"Name: {rule.name}")
                print(f"Type: {rule.rule_type}")
                print(f"Enabled: {rule.enabled}")
                print(f"Description: {rule.description or ''}")
                print("---")
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("info")
@pass_ctx_obj
@click.argument("rule_id", type=str)
def info_rule_cmd(ctx: CLIContext, rule_id: str) -> None:
    """
    Display detailed information of a notification rule.

    \b
    RULE_ID: The rule ID
    """
    with Session() as session:
        try:
            result = session.Notification.get_rule(UUID(rule_id))
            rule = result.rule
            print(json.dumps(rule.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("create")
@pass_ctx_obj
@click.argument("name", type=str)
@click.argument("rule_type", type=str)
@click.argument("channel_id", type=str)
@click.option("--template", type=str, default=None, help="Jinja2 template string")
@click.option(
    "--template-file",
    type=click.File("r"),
    default=None,
    help="Path to template file (use '-' for stdin)",
)
@click.option("--description", type=str, default=None, help="Rule description")
@click.option("--disabled", is_flag=True, help="Create rule as disabled")
def create_rule_cmd(
    ctx: CLIContext,
    name: str,
    rule_type: str,
    channel_id: str,
    template: Optional[str],
    template_file: Optional[IO],
    description: Optional[str],
    disabled: bool,
) -> None:
    """
    Create a new notification rule.

    \b
    NAME: Rule name
    RULE_TYPE: Type of rule (e.g., session.started, session.terminated)
    CHANNEL_ID: ID of the channel to use

    You must provide either --template or --template-file (but not both).
    """
    with Session() as session:
        try:
            # Validate template input
            if template and template_file:
                print_fail("Cannot specify both --template and --template-file")
                sys.exit(ExitCode.FAILURE)
            if not template and not template_file:
                print_fail("Must specify either --template or --template-file")
                sys.exit(ExitCode.FAILURE)

            # Get template content
            message_template = template_file.read() if template_file else template
            assert message_template is not None  # Already validated above

            request = CreateNotificationRuleRequest(
                name=name,
                rule_type=NotificationRuleType(rule_type),
                channel_id=UUID(channel_id),
                message_template=message_template,
                description=description,
                enabled=not disabled,
            )
            result = session.Notification.create_rule(request)
            rule = result.rule
            print_done(f"Rule created: {rule.id}")
            print(json.dumps(rule.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("update")
@pass_ctx_obj
@click.argument("rule_id", type=str)
@click.option("--name", type=str, default=None, help="Update rule name")
@click.option("--description", type=str, default=None, help="Update rule description")
@click.option("--message-template", type=str, default=None, help="Update message template string")
@click.option(
    "--template-file",
    type=click.File("r"),
    default=None,
    help="Path to template file (use '-' for stdin)",
)
@click.option("--enable", "enabled", flag_value=True, default=None, help="Enable the rule")
@click.option("--disable", "enabled", flag_value=False, default=None, help="Disable the rule")
def update_rule_cmd(
    ctx: CLIContext,
    rule_id: str,
    name: Optional[str],
    description: Optional[str],
    message_template: Optional[str],
    template_file: Optional[IO],
    enabled: Optional[bool],
) -> None:
    """
    Update a notification rule.

    \b
    RULE_ID: The rule ID to update

    Note: Cannot specify both --message-template and --template-file.
    """
    with Session() as session:
        try:
            # Validate template input
            if message_template and template_file:
                print_fail("Cannot specify both --message-template and --template-file")
                sys.exit(ExitCode.FAILURE)

            # Get template content if provided
            final_template = None
            if template_file:
                final_template = template_file.read()
            elif message_template:
                final_template = message_template

            request = UpdateNotificationRuleRequest(
                name=name,
                description=description,
                message_template=final_template,
                enabled=enabled,
            )
            result = session.Notification.update_rule(UUID(rule_id), request)
            rule = result.rule
            print_done(f"Rule updated: {rule_id}")
            print(json.dumps(rule.model_dump(mode="json"), indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("delete")
@pass_ctx_obj
@click.argument("rule_id", type=str)
def delete_rule_cmd(ctx: CLIContext, rule_id: str) -> None:
    """
    Delete a notification rule.

    \b
    RULE_ID: The rule ID to delete
    """
    with Session() as session:
        try:
            result = session.Notification.delete_rule(UUID(rule_id))
            if result.deleted:
                print_done(f"Rule deleted: {rule_id}")
            else:
                print_fail(f"Failed to delete rule: {rule_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("validate")
@pass_ctx_obj
@click.argument("rule_id", type=str)
@click.option(
    "--data",
    type=str,
    default=None,
    help='Test notification data as JSON string (e.g., \'{"session_id": "test"}\')',
)
@click.option(
    "--data-file",
    type=click.File("r"),
    default=None,
    help="Path to JSON file with test data (use '-' for stdin)",
)
def validate_rule_cmd(
    ctx: CLIContext, rule_id: str, data: Optional[str], data_file: Optional[IO]
) -> None:
    """
    Validate a notification rule by rendering its template with test data.

    \b
    RULE_ID: The rule ID to validate

    Note: Cannot specify both --data and --data-file.
    """
    with Session() as session:
        try:
            # Validate data input
            if data and data_file:
                print_fail("Cannot specify both --data and --data-file")
                sys.exit(ExitCode.FAILURE)

            # Get notification data
            notification_data = {}
            if data_file:
                notification_data = json.load(data_file)
            elif data:
                notification_data = json.loads(data)

            from ai.backend.common.dto.manager.notification import (
                ValidateNotificationRuleRequest,
            )

            request = ValidateNotificationRuleRequest(notification_data=notification_data)
            result = session.Notification.validate_rule(UUID(rule_id), request)

            print_done(f"Rule validation successful: {rule_id}")
            print("\nMessage:")
            print(result.message)
        except json.JSONDecodeError as e:
            print_fail(f"Invalid JSON data: {e}")
            sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
