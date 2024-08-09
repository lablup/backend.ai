from __future__ import annotations

from .formatters import (
    AgentStatFormatter,
    ContainerListFormatter,
    CustomizedImageOutputFormatter,
    DependencyListFormatter,
    GroupListFormatter,
    InlineRoutingFormatter,
    KernelStatFormatter,
    SubFieldOutputFormatter,
    mibytes_output_formatter,
    nested_dict_formatter,
    resource_slot_formatter,
    sizebytes_output_formatter,
)
from .types import FieldSet, FieldSpec

container_fields = FieldSet([
    FieldSpec("id", "Kernel ID", alt_name="kernel_id"),
    FieldSpec("cluster_role"),
    FieldSpec("cluster_idx"),
    FieldSpec("cluster_hostname"),
    FieldSpec("session_id", "Session ID"),
    FieldSpec("image"),
    FieldSpec("registry"),
    FieldSpec("status"),
    FieldSpec("status_info"),
    FieldSpec("status_data", formatter=nested_dict_formatter),
    FieldSpec("status_changed"),
    FieldSpec("agent"),
    FieldSpec("container_id"),
    FieldSpec("resource_opts", formatter=nested_dict_formatter),
    FieldSpec("occupied_slots", formatter=resource_slot_formatter),
    FieldSpec("preopen_ports", "Preopen Ports"),
    FieldSpec("live_stat", formatter=KernelStatFormatter()),
    FieldSpec("last_stat", formatter=KernelStatFormatter()),
])


agent_fields = FieldSet([
    FieldSpec("id"),
    FieldSpec("status"),
    FieldSpec("status_changed"),
    FieldSpec("region"),
    FieldSpec("architecture"),
    FieldSpec("scaling_group"),
    FieldSpec("schedulable"),
    FieldSpec("available_slots", formatter=resource_slot_formatter),
    FieldSpec("occupied_slots", formatter=resource_slot_formatter),
    FieldSpec("addr"),
    FieldSpec("first_contact"),
    FieldSpec("lost_at"),
    FieldSpec("live_stat", formatter=AgentStatFormatter()),
    FieldSpec("version"),
    FieldSpec("compute_plugins"),
    FieldSpec("hardware_metadata", formatter=nested_dict_formatter),
    FieldSpec("compute_containers", subfields=container_fields, formatter=ContainerListFormatter()),
    FieldSpec("local_config", formatter=nested_dict_formatter),
    # legacy fields
    FieldSpec("cpu_cur_pct", "CPU Usage (%)"),
    FieldSpec("mem_cur_bytes", "Used Memory (MiB)", formatter=mibytes_output_formatter),
])

domain_fields = FieldSet([
    FieldSpec("name"),
    FieldSpec("description"),
    FieldSpec("is_active"),
    FieldSpec("created_at"),
    FieldSpec("total_resource_slots", formatter=resource_slot_formatter),
    FieldSpec("allowed_vfolder_hosts"),
    FieldSpec("allowed_docker_registries"),
    FieldSpec("integration_id"),
])


group_fields = FieldSet([
    FieldSpec("id"),
    FieldSpec("name"),
    FieldSpec("description"),
    FieldSpec("is_active"),
    FieldSpec("created_at"),
    FieldSpec("domain_name"),
    FieldSpec("total_resource_slots", formatter=resource_slot_formatter),
    FieldSpec("allowed_vfolder_hosts"),
    FieldSpec("integration_id"),
])


image_fields = FieldSet([
    FieldSpec("id"),
    FieldSpec("name"),
    FieldSpec("registry"),
    FieldSpec("architecture"),
    FieldSpec("tag"),
    FieldSpec("digest"),
    FieldSpec("size_bytes", formatter=sizebytes_output_formatter),
    FieldSpec("aliases"),
    FieldSpec("labels { key value }", "labels"),
    FieldSpec(
        "labels { key value }",
        "Customized Image Info",
        alt_name="customized_image",
        formatter=CustomizedImageOutputFormatter(),
    ),
])


keypair_fields = FieldSet([
    FieldSpec("user_id", "Email"),
    FieldSpec(
        "user_info { full_name }",
        "Full Name",
        alt_name="full_name",
        formatter=SubFieldOutputFormatter("full_name"),
    ),
    FieldSpec("projects"),
    FieldSpec("access_key"),
    FieldSpec("secret_key"),
    FieldSpec("is_active"),
    FieldSpec("is_admin"),
    FieldSpec("created_at"),
    FieldSpec("modified_at"),
    FieldSpec("last_used"),
    FieldSpec("resource_policy"),
    FieldSpec("rate_limit"),
    FieldSpec("concurrency_used"),
    FieldSpec("ssh_public_key"),
    FieldSpec("ssh_private_key"),
    FieldSpec("dotfiles"),
    FieldSpec("bootstrap_script"),
])


keypair_resource_policy_fields = FieldSet([
    FieldSpec("name"),
    FieldSpec("created_at"),
    FieldSpec("total_resource_slots"),
    FieldSpec("max_session_lifetime"),
    FieldSpec("max_concurrent_sessions"),  # formerly concurrency_limit
    FieldSpec("idle_timeout"),
    FieldSpec("max_containers_per_session"),
    FieldSpec("allowed_vfolder_hosts"),
    FieldSpec("max_pending_session_count"),
    FieldSpec("max_pending_session_resource_slots"),
    FieldSpec("max_concurrent_sftp_sessions"),
])


scaling_group_fields = FieldSet([
    FieldSpec("name"),
    FieldSpec("description"),
    FieldSpec("is_active"),
    FieldSpec("is_public"),
    FieldSpec("created_at"),
    FieldSpec("driver"),
    FieldSpec("driver_opts", formatter=nested_dict_formatter),
    FieldSpec("scheduler"),
    FieldSpec("scheduler_opts", formatter=nested_dict_formatter),
    FieldSpec("use_host_network"),
    FieldSpec("wsproxy_addr"),
    FieldSpec("wsproxy_api_token"),
])


session_fields = FieldSet([
    FieldSpec("id", "Session ID", alt_name="session_id"),
    FieldSpec("main_kernel_id", "Main Kernel ID"),
    FieldSpec("tag"),
    FieldSpec("name"),
    FieldSpec("type"),
    FieldSpec("image"),
    FieldSpec("registry"),
    FieldSpec("cluster_template"),
    FieldSpec("cluster_mode"),
    FieldSpec("cluster_size"),
    FieldSpec("domain_name"),
    FieldSpec("group_name", "Project/Group"),
    FieldSpec("group_id"),
    FieldSpec("agent_ids"),
    FieldSpec("user_email"),
    FieldSpec("user_id"),
    FieldSpec("access_key", "Owner Access Key"),
    FieldSpec("created_user_email"),
    FieldSpec("created_user_id"),
    FieldSpec("status"),
    FieldSpec("status_info"),
    FieldSpec("status_data", formatter=nested_dict_formatter),
    FieldSpec("status_changed", "Last Updated"),
    FieldSpec("created_at"),
    FieldSpec("terminated_at"),
    FieldSpec("starts_at"),
    FieldSpec("scheduled_at"),
    FieldSpec("startup_command"),
    FieldSpec("result"),
    FieldSpec("resource_opts", formatter=nested_dict_formatter),
    FieldSpec("scaling_group"),
    FieldSpec("service_ports", formatter=nested_dict_formatter),
    FieldSpec("mounts"),
    FieldSpec("vfolder_mounts"),
    FieldSpec("occupying_slots", formatter=resource_slot_formatter),
    FieldSpec(
        "containers",
        subfields=container_fields,
        formatter=ContainerListFormatter(),
    ),
    FieldSpec(
        "dependencies { name id }",
        formatter=DependencyListFormatter(),
    ),
    FieldSpec("abusing_reports"),
    FieldSpec("idle_checks"),
])

session_fields_v5 = FieldSet([
    FieldSpec(
        "containers",
        subfields=FieldSet([
            FieldSpec("id", "Kernel ID", alt_name="kernel_id"),
            FieldSpec("session_id", "Session ID"),
            FieldSpec("role"),
            FieldSpec("agent"),
            FieldSpec("image"),
            FieldSpec("status"),
            FieldSpec("status_info"),
            FieldSpec("status_data", formatter=nested_dict_formatter),
            FieldSpec("status_changed"),
            FieldSpec("occupied_slots", formatter=resource_slot_formatter),
            FieldSpec("live_stat", formatter=KernelStatFormatter()),
            FieldSpec("last_stat", formatter=KernelStatFormatter()),
        ]),
        formatter=ContainerListFormatter(),
    ),
])


storage_fields = FieldSet([
    FieldSpec("id"),
    FieldSpec("backend"),
    FieldSpec("fsprefix"),
    FieldSpec("path"),
    FieldSpec("capabilities"),
    FieldSpec("hardware_metadata", formatter=nested_dict_formatter),
    FieldSpec("performance_metric", formatter=nested_dict_formatter),
    FieldSpec("usage", formatter=nested_dict_formatter),
])


user_fields = FieldSet([
    FieldSpec("uuid"),
    FieldSpec("username"),
    FieldSpec("email"),
    # password is not queriable!
    FieldSpec("need_password_change"),
    FieldSpec("full_name"),
    FieldSpec("description"),
    FieldSpec("is_active"),
    FieldSpec("status"),
    FieldSpec("status_info"),
    FieldSpec("created_at"),
    FieldSpec("modified_at"),
    FieldSpec("domain_name"),
    FieldSpec("role"),
    FieldSpec("groups { id name }", formatter=GroupListFormatter()),
    FieldSpec("allowed_client_ip"),
    FieldSpec("totp_activated"),
    FieldSpec("sudo_session_enabled"),
    FieldSpec("main_access_key"),
])


vfolder_fields = FieldSet([
    FieldSpec("id"),
    FieldSpec("host"),
    FieldSpec("name"),
    FieldSpec("user", alt_name="user_id"),
    FieldSpec("group", alt_name="group_id"),
    FieldSpec("creator"),
    FieldSpec("status"),
    FieldSpec("unmanaged_path"),
    FieldSpec("usage_mode"),
    FieldSpec("permission"),
    FieldSpec("ownership_type"),
    FieldSpec("max_files"),
    FieldSpec("max_size"),
    FieldSpec("created_at"),
    FieldSpec("last_used"),
    FieldSpec("num_files"),
    FieldSpec("cur_size"),
    FieldSpec("cloneable"),
])


permission_fields = FieldSet([
    FieldSpec("vfolder_host_permission_list"),
])


service_fields = FieldSet([
    FieldSpec("endpoint_id"),
    FieldSpec("image"),
    FieldSpec("domain"),
    FieldSpec("project"),
    FieldSpec("resource_group"),
    FieldSpec("resource_slots", formatter=nested_dict_formatter),
    FieldSpec("url"),
    FieldSpec("model"),
    FieldSpec("model_mount_destination"),
    FieldSpec("created_user"),
    FieldSpec("session_owner"),
    FieldSpec("tag"),
    FieldSpec("startup_command"),
    FieldSpec("bootstrap_script"),
    FieldSpec("callback_url"),
    FieldSpec("environ", formatter=nested_dict_formatter),
    FieldSpec("name"),
    FieldSpec("resource_opts", formatter=nested_dict_formatter),
    FieldSpec("desired_session_count"),
    FieldSpec("cluster_mode"),
    FieldSpec("cluster_size"),
    FieldSpec("open_to_public"),
    FieldSpec(
        "routings { routing_id session status traffic_ratio }",
        formatter=InlineRoutingFormatter(),
    ),
])


routing_fields = FieldSet([
    FieldSpec("routing_id"),
    FieldSpec("status"),
    FieldSpec("endpoint"),
    FieldSpec("session"),
    FieldSpec("traffic_ratio"),
])


quota_scope_fields = FieldSet([
    FieldSpec("usage_bytes", formatter=sizebytes_output_formatter),
    FieldSpec("usage_count"),
    FieldSpec("hard_limit_bytes", formatter=sizebytes_output_formatter),
    FieldSpec("quota_scope_id"),
    FieldSpec("storage_host_name"),
])
