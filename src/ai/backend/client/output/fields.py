from __future__ import annotations

from .formatters import (
    AgentStatFormatter,
    GroupListFormatter,
    ContainerListFormatter,
    DependencyListFormatter,
    SubFieldOutputFormatter,
    KernelStatFormatter,
    nested_dict_formatter,
    mibytes_output_formatter,
    resource_slot_formatter,
    sizebytes_output_formatter,
)
from .types import (
    FieldSet,
    FieldSpec,
)


container_fields = FieldSet([
    FieldSpec('id', "Kernel ID", alt_name='kernel_id'),
    FieldSpec('cluster_role'),
    FieldSpec('cluster_idx'),
    FieldSpec('cluster_hostname'),
    FieldSpec('session_id', "Session ID"),
    FieldSpec('image'),
    FieldSpec('registry'),
    FieldSpec('status'),
    FieldSpec('status_info'),
    FieldSpec('status_data', formatter=nested_dict_formatter),
    FieldSpec('status_changed'),
    FieldSpec('agent'),
    FieldSpec('container_id'),
    FieldSpec('resource_opts', formatter=nested_dict_formatter),
    FieldSpec('occupied_slots', formatter=resource_slot_formatter),
    FieldSpec('live_stat', formatter=KernelStatFormatter()),
    FieldSpec('last_stat', formatter=KernelStatFormatter()),
])


agent_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('status'),
    FieldSpec('status_changed'),
    FieldSpec('region'),
    FieldSpec('architecture'),
    FieldSpec('scaling_group'),
    FieldSpec('schedulable'),
    FieldSpec('available_slots', formatter=resource_slot_formatter),
    FieldSpec('occupied_slots', formatter=resource_slot_formatter),
    FieldSpec('addr'),
    FieldSpec('first_contact'),
    FieldSpec('lost_at'),
    FieldSpec('live_stat', formatter=AgentStatFormatter()),
    FieldSpec('version'),
    FieldSpec('compute_plugins'),
    FieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    FieldSpec('compute_containers', subfields=container_fields,
              formatter=ContainerListFormatter()),
    # legacy fields
    FieldSpec('cpu_cur_pct', 'CPU Usage (%)'),
    FieldSpec('mem_cur_bytes', 'Used Memory (MiB)', formatter=mibytes_output_formatter),
])

domain_fields = FieldSet([
    FieldSpec('name'),
    FieldSpec('description'),
    FieldSpec('is_active'),
    FieldSpec('created_at'),
    FieldSpec('total_resource_slots', formatter=resource_slot_formatter),
    FieldSpec('allowed_vfolder_hosts'),
    FieldSpec('allowed_docker_registries'),
    FieldSpec('integration_id'),
])

group_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('name'),
    FieldSpec('description'),
    FieldSpec('is_active'),
    FieldSpec('created_at'),
    FieldSpec('domain_name'),
    FieldSpec('total_resource_slots', formatter=resource_slot_formatter),
    FieldSpec('allowed_vfolder_hosts'),
    FieldSpec('integration_id'),
])


image_fields = FieldSet([
    FieldSpec('name'),
    FieldSpec('registry'),
    FieldSpec('architecture'),
    FieldSpec('tag'),
    FieldSpec('digest'),
    FieldSpec('size_bytes', formatter=sizebytes_output_formatter),
    FieldSpec('aliases'),
])


keypair_fields = FieldSet([
    FieldSpec('user_id', "Email"),
    FieldSpec('user_info { full_name }', "Full Name", alt_name='full_name',
              formatter=SubFieldOutputFormatter("full_name")),
    FieldSpec('access_key'),
    FieldSpec('secret_key'),
    FieldSpec('is_active'),
    FieldSpec('is_admin'),
    FieldSpec('created_at'),
    FieldSpec('modified_at'),
    FieldSpec('last_used'),
    FieldSpec('resource_policy'),
    FieldSpec('rate_limit'),
    FieldSpec('concurrency_used'),
    FieldSpec('ssh_public_key'),
    FieldSpec('ssh_private_key'),
    FieldSpec('dotfiles'),
    FieldSpec('bootstrap_script'),
])


keypair_resource_policy_fields = FieldSet([
    FieldSpec('name'),
    FieldSpec('created_at'),
    FieldSpec('total_resource_slots'),
    FieldSpec('max_concurrent_sessions'),  # formerly concurrency_limit
    FieldSpec('max_vfolder_count'),
    FieldSpec('max_vfolder_size', formatter=sizebytes_output_formatter),
    FieldSpec('idle_timeout'),
    FieldSpec('max_containers_per_session'),
    FieldSpec('allowed_vfolder_hosts'),
])


scaling_group_fields = FieldSet([
    FieldSpec('name'),
    FieldSpec('description'),
    FieldSpec('is_active'),
    FieldSpec('created_at'),
    FieldSpec('driver'),
    FieldSpec('driver_opts', formatter=nested_dict_formatter),
    FieldSpec('scheduler'),
    FieldSpec('scheduler_opts', formatter=nested_dict_formatter),
])


session_fields = FieldSet([
    FieldSpec('id', "Kernel ID", alt_name='kernel_id'),
    FieldSpec('tag'),
    FieldSpec('name'),
    FieldSpec('type'),
    FieldSpec('session_id', "Session ID"),
    FieldSpec('image'),
    FieldSpec('registry'),
    FieldSpec('cluster_template'),
    FieldSpec('cluster_mode'),
    FieldSpec('cluster_size'),
    FieldSpec('domain_name'),
    FieldSpec('group_name', "Project/Group"),
    FieldSpec('group_id'),
    FieldSpec('user_email'),
    FieldSpec('user_id'),
    FieldSpec('access_key', "Owner Access Key"),
    FieldSpec('created_user_email'),
    FieldSpec('created_user_id'),
    FieldSpec('status'),
    FieldSpec('status_info'),
    FieldSpec('status_data', formatter=nested_dict_formatter),
    FieldSpec('status_changed', "Last Updated"),
    FieldSpec('created_at'),
    FieldSpec('terminated_at'),
    FieldSpec('starts_at'),
    FieldSpec('startup_command'),
    FieldSpec('result'),
    FieldSpec('resoucre_opts', formatter=nested_dict_formatter),
    FieldSpec('scaling_group'),
    FieldSpec('service_ports', formatter=nested_dict_formatter),
    FieldSpec('mounts'),
    FieldSpec('occupied_slots', formatter=resource_slot_formatter),
    FieldSpec(
        'containers',
        subfields=container_fields,
        formatter=ContainerListFormatter(),
    ),
    FieldSpec(
        'dependencies { name id }',
        formatter=DependencyListFormatter(),
    ),
])

session_fields_v5 = FieldSet([
    FieldSpec(
        'containers',
        subfields=FieldSet([
            FieldSpec('id', "Kernel ID", alt_name='kernel_id'),
            FieldSpec('session_id', "Session ID"),
            FieldSpec('role'),
            FieldSpec('agent'),
            FieldSpec('image'),
            FieldSpec('status'),
            FieldSpec('status_info'),
            FieldSpec('status_data', formatter=nested_dict_formatter),
            FieldSpec('status_changed'),
            FieldSpec('occupied_slots', formatter=resource_slot_formatter),
            FieldSpec('live_stat', formatter=KernelStatFormatter()),
            FieldSpec('last_stat', formatter=KernelStatFormatter()),
        ]),
        formatter=ContainerListFormatter(),
    ),
])


storage_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('backend'),
    FieldSpec('fsprefix'),
    FieldSpec('path'),
    FieldSpec('capabilities'),
    FieldSpec('hardware_metadata', formatter=nested_dict_formatter),
    FieldSpec('performance_metric', formatter=nested_dict_formatter),
    FieldSpec('usage', formatter=nested_dict_formatter),
])


user_fields = FieldSet([
    FieldSpec('uuid'),
    FieldSpec('username'),
    FieldSpec('email'),
    # password is not queriable!
    FieldSpec('need_password_change'),
    FieldSpec('full_name'),
    FieldSpec('description'),
    FieldSpec('is_active'),
    FieldSpec('status'),
    FieldSpec('status_info'),
    FieldSpec('created_at'),
    FieldSpec('modified_at'),
    FieldSpec('domain_name'),
    FieldSpec('role'),
    FieldSpec('groups { id name }', formatter=GroupListFormatter()),
])


vfolder_fields = FieldSet([
    FieldSpec('id'),
    FieldSpec('host'),
    FieldSpec('name'),
    FieldSpec('user', alt_name='user_id'),
    FieldSpec('group', alt_name='group_id'),
    FieldSpec('creator'),
    FieldSpec('unmanaged_path'),
    FieldSpec('usage_mode'),
    FieldSpec('permission'),
    FieldSpec('ownership_type'),
    FieldSpec('max_files'),
    FieldSpec('max_size'),
    FieldSpec('created_at'),
    FieldSpec('last_used'),
    FieldSpec('num_files'),
    FieldSpec('cur_size'),
    FieldSpec('cloneable'),
])
