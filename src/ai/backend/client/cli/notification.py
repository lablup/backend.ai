"""CLI commands for notification system."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from ai.backend.cli.main import main
from ai.backend.cli.types import ExitCode
from ai.backend.client.session import Session

from .extensions import pass_ctx_obj
from .pretty import print_done, print_fail
from .types import CLIContext


@main.group()
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
            result = session.Notification.list_channels(enabled_only=enabled_only)
            channels = result.get("channels", [])
            if not channels:
                print("No channels found")
                return
            for channel in channels:
                print(f"ID: {channel.get('id')}")
                print(f"Name: {channel.get('name')}")
                print(f"Type: {channel.get('channel_type')}")
                print(f"Enabled: {channel.get('enabled')}")
                print(f"Description: {channel.get('description', '')}")
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
            result = session.Notification.get_channel(channel_id)
            channel = result.get("channel", {})
            print(json.dumps(channel, indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@channel.command("create")
@pass_ctx_obj
@click.argument("name", type=str)
@click.argument("url", type=str)
@click.option("--channel-type", default="WEBHOOK", help="Channel type (default: WEBHOOK)")
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
            config = {"url": url}

            result = session.Notification.create_channel(
                name=name,
                channel_type=channel_type,
                config=config,
                description=description,
                enabled=not disabled,
            )
            channel = result.get("channel", {})
            print_done(f"Channel created: {channel.get('id')}")
            print(json.dumps(channel, indent=2, default=str))
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
                config = {"url": url}

            result = session.Notification.update_channel(
                channel_id=channel_id,
                name=name,
                description=description,
                config=config,
                enabled=enabled,
            )
            channel = result.get("channel", {})
            print_done(f"Channel updated: {channel_id}")
            print(json.dumps(channel, indent=2, default=str))
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
            result = session.Notification.delete_channel(channel_id)
            if result.get("deleted", False):
                print_done(f"Channel deleted: {channel_id}")
            else:
                print_fail(f"Failed to delete channel: {channel_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


# Rule commands


@notification.group()
def rule():
    """Manage notification rules"""


@rule.command("list")
@pass_ctx_obj
@click.option("--enabled-only", is_flag=True, help="Only list enabled rules")
@click.option("--rule-type", type=str, default=None, help="Filter by rule type")
def list_rules_cmd(ctx: CLIContext, enabled_only: bool, rule_type: Optional[str]) -> None:
    """
    List all notification rules.
    """
    with Session() as session:
        try:
            result = session.Notification.list_rules(
                enabled_only=enabled_only,
                rule_type=rule_type,
            )
            rules = result.get("rules", [])
            if not rules:
                print("No rules found")
                return
            for rule in rules:
                print(f"ID: {rule.get('id')}")
                print(f"Name: {rule.get('name')}")
                print(f"Type: {rule.get('rule_type')}")
                print(f"Enabled: {rule.get('enabled')}")
                print(f"Description: {rule.get('description', '')}")
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
            result = session.Notification.get_rule(rule_id)
            rule = result.get("rule", {})
            print(json.dumps(rule, indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("create")
@pass_ctx_obj
@click.argument("name", type=str)
@click.argument("rule_type", type=str)
@click.argument("channel_id", type=str)
@click.argument("message_template", type=str)
@click.option("--description", type=str, default=None, help="Rule description")
@click.option("--disabled", is_flag=True, help="Create rule as disabled")
def create_rule_cmd(
    ctx: CLIContext,
    name: str,
    rule_type: str,
    channel_id: str,
    message_template: str,
    description: Optional[str],
    disabled: bool,
) -> None:
    """
    Create a new notification rule.

    \b
    NAME: Rule name
    RULE_TYPE: Type of rule (e.g., SESSION_STARTED, SESSION_TERMINATED)
    CHANNEL_ID: ID of the channel to use
    MESSAGE_TEMPLATE: Jinja2 template for notification message
    """
    with Session() as session:
        try:
            result = session.Notification.create_rule(
                name=name,
                rule_type=rule_type,
                channel_id=channel_id,
                message_template=message_template,
                description=description,
                enabled=not disabled,
            )
            rule = result.get("rule", {})
            print_done(f"Rule created: {rule.get('id')}")
            print(json.dumps(rule, indent=2, default=str))
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)


@rule.command("update")
@pass_ctx_obj
@click.argument("rule_id", type=str)
@click.option("--name", type=str, default=None, help="Update rule name")
@click.option("--description", type=str, default=None, help="Update rule description")
@click.option("--message-template", type=str, default=None, help="Update message template")
@click.option("--enable", "enabled", flag_value=True, default=None, help="Enable the rule")
@click.option("--disable", "enabled", flag_value=False, default=None, help="Disable the rule")
def update_rule_cmd(
    ctx: CLIContext,
    rule_id: str,
    name: Optional[str],
    description: Optional[str],
    message_template: Optional[str],
    enabled: Optional[bool],
) -> None:
    """
    Update a notification rule.

    \b
    RULE_ID: The rule ID to update
    """
    with Session() as session:
        try:
            result = session.Notification.update_rule(
                rule_id=rule_id,
                name=name,
                description=description,
                message_template=message_template,
                enabled=enabled,
            )
            rule = result.get("rule", {})
            print_done(f"Rule updated: {rule_id}")
            print(json.dumps(rule, indent=2, default=str))
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
            result = session.Notification.delete_rule(rule_id)
            if result.get("deleted", False):
                print_done(f"Rule deleted: {rule_id}")
            else:
                print_fail(f"Failed to delete rule: {rule_id}")
                sys.exit(ExitCode.FAILURE)
        except Exception as e:
            ctx.output.print_error(e)
            sys.exit(ExitCode.FAILURE)
