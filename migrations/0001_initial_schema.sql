-- Initial schema of the Go rewrite.
-- Source: the manager schema at commit 4829aed7fe (the commit `v2` was created from),
-- alembic revision ae624fa26235 (head), created with `mgr schema oneshot`.
-- The alembic_version table is not included.

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: agentstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agentstatus AS ENUM (
    'ALIVE',
    'LOST',
    'RESTARTING',
    'TERMINATED'
);


--
-- Name: artifacttype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.artifacttype AS ENUM (
    'MODEL',
    'PACKAGE',
    'IMAGE'
);


--
-- Name: defaultforunspecified; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.defaultforunspecified AS ENUM (
    'LIMITED',
    'UNLIMITED'
);


--
-- Name: errorlog_severity; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.errorlog_severity AS ENUM (
    'critical',
    'error',
    'warning'
);


--
-- Name: imagetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.imagetype AS ENUM (
    'COMPUTE',
    'SYSTEM',
    'SERVICE'
);


--
-- Name: templatetype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.templatetype AS ENUM (
    'TASK',
    'CLUSTER'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'superadmin',
    'admin',
    'user',
    'monitor'
);


--
-- Name: userstatus; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userstatus AS ENUM (
    'active',
    'inactive',
    'deleted',
    'before-verification',
    'purging',
    'purge-error'
);


--
-- Name: vfolderownershiptype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vfolderownershiptype AS ENUM (
    'user',
    'group'
);


--
-- Name: vfolderusagemode; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.vfolderusagemode AS ENUM (
    'general',
    'model',
    'data'
);


--
-- Name: uuid_generate_v7(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.uuid_generate_v7() RETURNS uuid
    LANGUAGE plpgsql
    AS $$
DECLARE
  ticks bigint;
  last  bigint;
BEGIN
  ticks := floor(extract(epoch FROM clock_timestamp()) * 1000 * 4096)::bigint;
  last := NULLIF(current_setting('backendai.uuid7_last', true), '')::bigint;
  IF last IS NOT NULL AND ticks <= last THEN
    ticks := last + 1;
  END IF;
  PERFORM set_config('backendai.uuid7_last', ticks::text, false);
  RETURN encode(
    overlay(
      overlay(uuid_send(gen_random_uuid())
        placing substring(int8send(ticks >> 12) from 3) from 1 for 6)
      placing int2send((x'7000'::int | (ticks & 4095)::int)::int2) from 7 for 2
    ), 'hex')::uuid;
END $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_installed_images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_installed_images (
    agent_id character varying(64) NOT NULL,
    image_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: agent_resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_resources (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    agent_id character varying(64) NOT NULL,
    agent_uuid uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    capacity numeric(24,6) NOT NULL,
    reserved numeric(24,6) DEFAULT 0 NOT NULL,
    prereserved numeric(24,6) DEFAULT 0 NOT NULL,
    used numeric(24,6) DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agents (
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    id character varying(64) NOT NULL,
    status public.agentstatus NOT NULL,
    status_changed timestamp with time zone,
    region character varying(64) NOT NULL,
    scaling_group character varying(64) DEFAULT 'default'::character varying NOT NULL,
    resource_group_id uuid NOT NULL,
    schedulable boolean DEFAULT true NOT NULL,
    addr character varying(128) NOT NULL,
    public_host character varying(256),
    public_key character varying(40),
    first_contact timestamp with time zone DEFAULT now(),
    lost_at timestamp with time zone,
    version character varying(64) NOT NULL,
    architecture character varying(32) NOT NULL,
    compute_plugins jsonb NOT NULL,
    auto_terminate_abusing_kernel boolean DEFAULT false NOT NULL
);


--
-- Name: app_config_allow_list; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_config_allow_list (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    config_name character varying(128) NOT NULL,
    scope_type character varying(64) NOT NULL,
    rank integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: app_config_definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_config_definitions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    config_name character varying(128) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: app_config_fragments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_config_fragments (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    config_name character varying(128) NOT NULL,
    scope_type character varying(64) NOT NULL,
    scope_id uuid,
    config jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_app_config_fragments_scope_id_matches_scope_type CHECK ((((scope_type)::text = 'public'::text) = (scope_id IS NULL)))
);


--
-- Name: artifact_registries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_registries (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying NOT NULL,
    registry_id uuid NOT NULL,
    type character varying NOT NULL
);


--
-- Name: artifact_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifact_revisions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    artifact_id uuid NOT NULL,
    version character varying NOT NULL,
    readme text,
    size bigint,
    digest character varying,
    status character varying NOT NULL,
    remote_status character varying,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    verification_result json
);


--
-- Name: artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifacts (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    type public.artifacttype NOT NULL,
    name character varying NOT NULL,
    registry_id uuid NOT NULL,
    registry_type character varying NOT NULL,
    source_registry_id uuid NOT NULL,
    source_registry_type character varying NOT NULL,
    description character varying,
    readonly boolean NOT NULL,
    extra json,
    scanned_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    availability character varying DEFAULT 'ALIVE'::character varying NOT NULL
);


--
-- Name: association_artifacts_storages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.association_artifacts_storages (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    artifact_revision_id uuid NOT NULL,
    storage_namespace_id uuid NOT NULL,
    storage_type character varying NOT NULL
);


--
-- Name: association_container_registries_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.association_container_registries_groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    registry_id uuid NOT NULL,
    project_id uuid NOT NULL,
    is_default boolean DEFAULT false NOT NULL
);


--
-- Name: association_groups_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.association_groups_users (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    user_id uuid NOT NULL,
    group_id uuid NOT NULL
);


--
-- Name: audit_log_scopes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log_scopes (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    audit_log_id uuid NOT NULL,
    scope_type character varying NOT NULL,
    scope_id uuid NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    action_kind character varying(64),
    entity_type character varying,
    operation character varying NOT NULL,
    action_name character varying NOT NULL,
    entity_id uuid,
    lookup_kind character varying,
    lookup_key character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    action_id uuid NOT NULL,
    request_id character varying,
    triggered_by character varying,
    acted_as uuid,
    description character varying NOT NULL,
    duration interval,
    client_ip inet,
    status character varying(64) NOT NULL
);


--
-- Name: auto_generated_file_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_generated_file_revisions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    file_id uuid NOT NULL,
    revision_number integer NOT NULL,
    data text NOT NULL,
    perm text NOT NULL,
    creator_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_auto_generated_file_revisions_data_length CHECK ((char_length(data) <= 65536)),
    CONSTRAINT ck_auto_generated_file_revisions_perm_length CHECK ((char_length(perm) <= 4))
);


--
-- Name: auto_generated_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auto_generated_files (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id uuid NOT NULL,
    path text NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: bootstrap_script_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bootstrap_script_revisions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    script_id uuid NOT NULL,
    revision_number integer NOT NULL,
    script text NOT NULL,
    creator_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_bootstrap_script_revisions_script_length CHECK ((char_length(script) <= 65536))
);


--
-- Name: bootstrap_scripts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bootstrap_scripts (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: client_ip_masking_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_ip_masking_policies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    target_type character varying(64) NOT NULL,
    mode character varying(64) NOT NULL,
    ipv4_prefix smallint,
    ipv6_prefix smallint,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_client_ip_masking_policies_ck_client_ip_masking_poli_3853 CHECK (((ipv4_prefix IS NULL) OR ((ipv4_prefix >= 0) AND (ipv4_prefix <= 32)))),
    CONSTRAINT ck_client_ip_masking_policies_ck_client_ip_masking_poli_dec7 CHECK (((ipv6_prefix IS NULL) OR ((ipv6_prefix >= 0) AND (ipv6_prefix <= 128))))
);


--
-- Name: container_registries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.container_registries (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    url character varying(512) NOT NULL,
    registry_name character varying(255) NOT NULL,
    type character varying(64) DEFAULT 'docker'::character varying NOT NULL,
    project character varying(255),
    username character varying(255),
    password character varying,
    ssl_verify boolean DEFAULT true,
    is_global boolean DEFAULT true NOT NULL,
    extra json
);


--
-- Name: deployment_auto_scaling_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_auto_scaling_policies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    endpoint uuid NOT NULL,
    min_replicas integer DEFAULT 1 NOT NULL,
    max_replicas integer DEFAULT 10 NOT NULL,
    metric_source character varying(64),
    metric_name text,
    comparator character varying(64),
    scale_up_threshold character varying,
    scale_down_threshold character varying,
    scale_up_step_size integer DEFAULT 1 NOT NULL,
    scale_down_step_size integer DEFAULT 1 NOT NULL,
    cooldown_seconds integer DEFAULT 300 NOT NULL,
    last_scaled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: deployment_designated_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_designated_agents (
    endpoint_id uuid NOT NULL,
    agent_uuid uuid NOT NULL
);


--
-- Name: deployment_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_history (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    deployment_id uuid NOT NULL,
    handler_category character varying(64) DEFAULT 'lifecycle'::character varying NOT NULL,
    phase character varying(64) NOT NULL,
    from_status character varying(64),
    to_status character varying(64),
    result character varying(32) NOT NULL,
    error_code character varying(128),
    message text NOT NULL,
    sub_steps jsonb DEFAULT '[]'::jsonb NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: deployment_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_policies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    endpoint uuid NOT NULL,
    strategy character varying(64) NOT NULL,
    strategy_spec jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: deployment_revision_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_revision_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    runtime_variant uuid NOT NULL,
    name character varying(256) NOT NULL,
    description text,
    rank integer NOT NULL,
    image_id uuid NOT NULL,
    model_definition jsonb,
    resource_opts jsonb DEFAULT '[]'::jsonb NOT NULL,
    cluster_mode character varying(16) DEFAULT 'single-node'::character varying NOT NULL,
    cluster_size integer DEFAULT 1 NOT NULL,
    startup_command text,
    bootstrap_script text,
    environ jsonb DEFAULT '{}'::jsonb NOT NULL,
    preset_values jsonb DEFAULT '[]'::jsonb NOT NULL,
    open_to_public boolean,
    replica_count integer DEFAULT 1 NOT NULL,
    revision_history_limit integer,
    deployment_strategy character varying(64) DEFAULT 'ROLLING'::character varying NOT NULL,
    deployment_strategy_spec jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: deployment_revision_resource_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_revision_resource_slots (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    revision_id uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    quantity numeric(24,6) NOT NULL
);


--
-- Name: deployment_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_revisions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    endpoint uuid NOT NULL,
    revision_number integer NOT NULL,
    image uuid,
    model uuid,
    model_mount_destination character varying(1024) DEFAULT '/models'::character varying NOT NULL,
    vfolder_subpath character varying(1024),
    model_definition_path character varying(128),
    model_definition jsonb,
    model_mount_perm character varying(64) DEFAULT 'ro'::character varying NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_opts jsonb DEFAULT '{}'::jsonb NOT NULL,
    cluster_mode character varying(16) DEFAULT 'SINGLE_NODE'::character varying NOT NULL,
    cluster_size integer DEFAULT 1 NOT NULL,
    startup_command text,
    bootstrap_script character varying(16384),
    environ jsonb DEFAULT '{}'::jsonb NOT NULL,
    callback_url text,
    runtime_variant_id uuid NOT NULL,
    termination_grace_period double precision DEFAULT '30'::double precision NOT NULL,
    extra_mounts jsonb DEFAULT '[]'::jsonb NOT NULL,
    preset_values jsonb DEFAULT '[]'::jsonb NOT NULL,
    revision_preset_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: domain_container_registry_relations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.domain_container_registry_relations (
    domain_id uuid NOT NULL,
    container_registry_id uuid NOT NULL
);


--
-- Name: domain_fair_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.domain_fair_shares (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    weight numeric(10,4),
    fair_share_factor numeric(8,6) NOT NULL,
    total_decayed_usage jsonb NOT NULL,
    resource_weights jsonb NOT NULL,
    normalized_usage numeric(8,6) NOT NULL,
    last_calculated_at timestamp with time zone DEFAULT now() NOT NULL,
    lookback_start date DEFAULT CURRENT_DATE NOT NULL,
    lookback_end date DEFAULT CURRENT_DATE NOT NULL,
    half_life_days integer NOT NULL,
    lookback_days integer NOT NULL,
    decay_unit_days integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN domain_fair_shares.weight; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.weight IS 'Priority weight multiplier. Higher weight = higher priority allocation ratio. Example: 2.0 means 2x priority compared to default 1.0. NULL means use resource group''s default_weight.';


--
-- Name: COLUMN domain_fair_shares.fair_share_factor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.fair_share_factor IS 'Calculated priority score from 0.0 to 1.0. Higher value = less past usage = higher scheduling priority. Formula: F = 2^(-normalized_usage / weight)';


--
-- Name: COLUMN domain_fair_shares.total_decayed_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.total_decayed_usage IS 'Sum of historical resource usage with time decay applied. Unit: resource-seconds (e.g., cpu-seconds, mem-seconds). Older usage is weighted less via half-life decay.';


--
-- Name: COLUMN domain_fair_shares.resource_weights; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.resource_weights IS 'Resource weights used in fair share calculation. From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}';


--
-- Name: COLUMN domain_fair_shares.normalized_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.normalized_usage IS 'Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). Both usage and capacity are in resource-seconds. Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])';


--
-- Name: COLUMN domain_fair_shares.last_calculated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.last_calculated_at IS 'Timestamp when fair_share_factor was last recalculated by batch job.';


--
-- Name: COLUMN domain_fair_shares.lookback_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.lookback_start IS 'Start date of the usage history window used in last calculation. Typically: today - lookback_days.';


--
-- Name: COLUMN domain_fair_shares.lookback_end; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.lookback_end IS 'End date of the usage history window used in last calculation. Typically: today.';


--
-- Name: COLUMN domain_fair_shares.half_life_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.half_life_days IS 'Number of days for usage to decay to 50%%. Example: 7 means usage from 7 days ago counts as 50%% of recent usage.';


--
-- Name: COLUMN domain_fair_shares.lookback_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.lookback_days IS 'Number of days of usage history to consider for fair share calculation. Example: 28 means only last 28 days of usage affects priority.';


--
-- Name: COLUMN domain_fair_shares.decay_unit_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_fair_shares.decay_unit_days IS 'Aggregation period for usage buckets in days. Example: 1 means daily aggregation, 7 means weekly aggregation.';


--
-- Name: domain_usage_buckets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.domain_usage_buckets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    domain_name character varying(64) NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    decay_unit_days integer NOT NULL,
    resource_usage jsonb NOT NULL,
    capacity_snapshot jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN domain_usage_buckets.capacity_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.domain_usage_buckets.capacity_snapshot IS 'Scaling group capacity at bucket period. Sum of agent.available_slots for calculating usage ratio.';


--
-- Name: domains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.domains (
    name character varying(64) NOT NULL,
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    description character varying(512),
    is_active boolean NOT NULL,
    status character varying(64) DEFAULT 'active'::character varying NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    total_resource_slots jsonb NOT NULL,
    allowed_vfolder_hosts jsonb NOT NULL,
    allowed_docker_registries character varying[] NOT NULL,
    integration_id character varying(512),
    dotfiles bytea NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: endpoint_auto_scaling_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.endpoint_auto_scaling_rules (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    metric_source character varying(64) NOT NULL,
    metric_name text NOT NULL,
    min_threshold character varying,
    max_threshold character varying,
    step_size integer NOT NULL,
    cooldown_seconds integer NOT NULL,
    min_replicas integer,
    max_replicas integer,
    prometheus_query_preset_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_triggered_at timestamp with time zone,
    endpoint uuid NOT NULL
);


--
-- Name: endpoint_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.endpoint_tokens (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    token character varying NOT NULL,
    endpoint uuid NOT NULL,
    session_owner uuid NOT NULL,
    domain character varying(64) NOT NULL,
    project uuid NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: endpoints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.endpoints (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(512) NOT NULL,
    created_user uuid NOT NULL,
    session_owner uuid NOT NULL,
    replicas integer DEFAULT 0 NOT NULL,
    desired_replicas integer,
    domain character varying(64) NOT NULL,
    project uuid NOT NULL,
    resource_group character varying NOT NULL,
    lifecycle_stage character varying(64) NOT NULL,
    scaling_state character varying(64) DEFAULT 'stable'::character varying NOT NULL,
    tag character varying(64),
    open_to_public boolean,
    url character varying(1024),
    retries integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    destroyed_at timestamp with time zone,
    primary_replica_group_id uuid,
    target_replica_group_id uuid,
    deploying_revision_id uuid,
    sub_step character varying(64),
    revision_history_limit integer DEFAULT 10 NOT NULL,
    options jsonb NOT NULL
);


--
-- Name: entity_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_fields (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    entity_type character varying(64) NOT NULL,
    entity_id character varying(64) NOT NULL,
    field_type character varying(64) NOT NULL,
    field_id character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: entity_labels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_labels (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id uuid NOT NULL,
    key character varying(255) NOT NULL,
    value character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: entity_membership_caps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_membership_caps (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    membership_id uuid NOT NULL,
    permission smallint NOT NULL,
    all_fields boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_entity_membership_caps_field_scope CHECK ((all_fields OR (permission = ANY (ARRAY[1, 2])))),
    CONSTRAINT ck_entity_membership_caps_single_bit CHECK (((permission > 0) AND (((permission)::integer & (permission - 1)) = 0)))
);


--
-- Name: entity_membership_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_membership_fields (
    cap_id uuid NOT NULL,
    path text NOT NULL,
    CONSTRAINT ck_entity_membership_fields_path CHECK ((path <> ''::text))
);


--
-- Name: entity_memberships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_memberships (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    virtual_entity_id uuid NOT NULL,
    member_entity_id uuid NOT NULL,
    capped boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: entity_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_shares (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    sharer_user_id uuid,
    recipient_entity_type character varying(32),
    recipient_entity_id uuid,
    recipient_email character varying(64),
    target_entity_type character varying(32) NOT NULL,
    target_entity_id uuid NOT NULL,
    permission_cap smallint,
    expires_at timestamp with time zone,
    status character varying(64) DEFAULT 'pending'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_entity_shares_accepted_does_not_expire CHECK ((((status)::text <> 'accepted'::text) OR (expires_at IS NULL))),
    CONSTRAINT ck_entity_shares_accepted_resolved CHECK ((((status)::text <> 'accepted'::text) OR (recipient_entity_type IS NOT NULL))),
    CONSTRAINT ck_entity_shares_addressed CHECK (((recipient_entity_type IS NOT NULL) OR (recipient_email IS NOT NULL)))
);


--
-- Name: error_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.error_logs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    severity public.errorlog_severity,
    source character varying,
    "user" uuid,
    is_read boolean,
    is_cleared boolean,
    message text,
    context_lang character varying,
    context_env jsonb,
    request_url character varying,
    request_status integer,
    traceback text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: event_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_logs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    event_name character varying NOT NULL,
    event_domain character varying(64) NOT NULL,
    domain_id character varying,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    duration interval
);


--
-- Name: global_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.global_entities (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(32) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    description character varying(512),
    is_active boolean,
    status character varying(64) DEFAULT 'active'::character varying NOT NULL,
    integration_id character varying(512),
    domain_name character varying(64) NOT NULL,
    total_resource_slots jsonb NOT NULL,
    allowed_vfolder_hosts jsonb NOT NULL,
    dotfiles bytea NOT NULL,
    resource_policy character varying(256) NOT NULL,
    type character varying(64) NOT NULL,
    creator_id uuid,
    container_registry jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: huggingface_registries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.huggingface_registries (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    url character varying NOT NULL,
    token character varying
);


--
-- Name: idle_checker_bindings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.idle_checker_bindings (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    scope_type character varying(64) NOT NULL,
    scope_id uuid NOT NULL,
    idle_checker_id uuid NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: idle_checkers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.idle_checkers (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    checker_type character varying(64) GENERATED ALWAYS AS ((spec ->> 'type'::text)) STORED NOT NULL,
    target_session_types character varying(64)[] NOT NULL,
    initial_grace_period_seconds integer DEFAULT 0 NOT NULL,
    spec jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_idle_checkers_initial_grace_period_seconds_non_negative CHECK ((initial_grace_period_seconds >= 0))
);


--
-- Name: image_aliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.image_aliases (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    alias character varying,
    image uuid NOT NULL
);


--
-- Name: images; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.images (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying NOT NULL,
    project character varying,
    image character varying NOT NULL,
    tag text,
    registry character varying NOT NULL,
    registry_id uuid NOT NULL,
    architecture character varying NOT NULL,
    config_digest character(72) NOT NULL,
    size_bytes bigint NOT NULL,
    is_local boolean DEFAULT false NOT NULL,
    type public.imagetype NOT NULL,
    accelerators character varying,
    labels json NOT NULL,
    customized boolean DEFAULT false NOT NULL,
    creator_id uuid,
    resources jsonb NOT NULL,
    status character varying(64) DEFAULT 'ALIVE'::character varying NOT NULL,
    last_used_at timestamp with time zone DEFAULT now() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kernel_group_environ; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_group_environ (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_group_id uuid NOT NULL,
    key character varying(256) NOT NULL,
    value text NOT NULL,
    CONSTRAINT ck_kernel_group_environ_key_is_environ_name CHECK (((key)::text ~ '^[A-Za-z_][A-Za-z0-9_]*$'::text))
);


--
-- Name: kernel_group_resource_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_group_resource_slots (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_group_id uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    quantity numeric(24,6) NOT NULL
);


--
-- Name: kernel_group_vfolder_mounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_group_vfolder_mounts (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_group_id uuid NOT NULL,
    vfolder_id uuid NOT NULL,
    vfsubpath text NOT NULL,
    mount_destination text NOT NULL,
    mount_perm character varying(64) NOT NULL
);


--
-- Name: kernel_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_id uuid NOT NULL,
    role character varying(16) NOT NULL,
    image_id uuid,
    shmem bigint,
    startup_command text,
    preopen_ports integer[] DEFAULT '{}'::integer[] NOT NULL,
    requested_starts_at timestamp with time zone,
    batch_timeout_sec integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: kernel_scheduling_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_scheduling_history (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_id uuid NOT NULL,
    session_id uuid NOT NULL,
    phase character varying(64) NOT NULL,
    from_status character varying(64),
    to_status character varying(64),
    result character varying(32) NOT NULL,
    error_code character varying(128),
    message text NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: kernel_usage_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernel_usage_records (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_id uuid NOT NULL,
    session_id uuid NOT NULL,
    user_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    resource_usage jsonb NOT NULL
);


--
-- Name: kernels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.kernels (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_id uuid NOT NULL,
    kernel_group_id uuid,
    session_creation_id character varying(32),
    session_name character varying(128),
    session_type character varying(64) DEFAULT 'INTERACTIVE'::character varying NOT NULL,
    cluster_mode character varying(16) DEFAULT 'SINGLE_NODE'::character varying NOT NULL,
    cluster_size integer NOT NULL,
    cluster_role character varying(16) NOT NULL,
    cluster_idx integer NOT NULL,
    local_rank integer NOT NULL,
    cluster_hostname character varying(64) NOT NULL,
    uid integer,
    main_gid integer,
    gids integer[],
    scaling_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    agent character varying(64),
    agent_addr character varying(128),
    domain_name character varying(64) NOT NULL,
    group_id uuid NOT NULL,
    user_uuid uuid,
    access_key character varying(20),
    image character varying(512),
    image_id uuid,
    architecture character varying(32),
    registry character varying(512),
    tag character varying(64),
    container_id character varying(64),
    occupied_shares jsonb NOT NULL,
    environ character varying[],
    mounts character varying[],
    mount_map jsonb,
    vfolder_mounts jsonb,
    attached_devices jsonb,
    resource_opts jsonb,
    bootstrap_script character varying(16384),
    kernel_host character varying(128),
    repl_in_port integer NOT NULL,
    repl_out_port integer NOT NULL,
    stdin_port integer NOT NULL,
    stdout_port integer NOT NULL,
    service_ports jsonb,
    preopen_ports integer[],
    use_host_network boolean NOT NULL,
    terminated_at timestamp with time zone,
    starts_at timestamp with time zone,
    status character varying(64) DEFAULT 'PENDING'::character varying NOT NULL,
    status_changed timestamp with time zone,
    status_info character varying,
    status_data jsonb,
    status_history jsonb,
    callback_url text,
    startup_command text,
    result character varying(64) DEFAULT 'UNDEFINED'::character varying NOT NULL,
    internal_data jsonb,
    container_log bytea,
    num_queries bigint,
    last_stat jsonb,
    last_seen timestamp with time zone,
    last_observed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: keypair_resource_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.keypair_resource_policies (
    name character varying(256) NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    default_for_unspecified public.defaultforunspecified NOT NULL,
    total_resource_slots jsonb NOT NULL,
    max_session_lifetime integer DEFAULT 0 NOT NULL,
    max_concurrent_sessions integer NOT NULL,
    max_pending_session_count integer,
    max_pending_session_resource_slots jsonb,
    max_priority integer,
    max_concurrent_sftp_sessions integer DEFAULT 1 NOT NULL,
    max_containers_per_session integer NOT NULL,
    idle_timeout bigint NOT NULL,
    allowed_vfolder_hosts jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_keypair_resource_policies_max_priority_within_sessio_6505 CHECK (((max_priority >= 0) AND (max_priority <= 100)))
);


--
-- Name: keypairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.keypairs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    access_key character varying(20) NOT NULL,
    secret_key text NOT NULL,
    is_active boolean NOT NULL,
    is_admin boolean DEFAULT false NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    last_used timestamp with time zone,
    rate_limit integer DEFAULT 10000 NOT NULL,
    num_queries integer DEFAULT 0 NOT NULL,
    ssh_public_key text,
    ssh_private_key text,
    "user" uuid NOT NULL,
    resource_policy character varying(256) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: login_client_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_client_types (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: login_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_history (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    user_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    result character varying(64) NOT NULL,
    fail_reason text,
    client_ip inet,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: login_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_sessions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_token character varying(64) NOT NULL,
    user_id uuid NOT NULL,
    access_key character varying(20) NOT NULL,
    login_client_type_id uuid,
    status character varying(64) DEFAULT 'active'::character varying NOT NULL,
    last_accessed_at timestamp with time zone,
    invalidated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: model_card_resource_requirements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_card_resource_requirements (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    model_card_id uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    min_quantity numeric(24,6) NOT NULL
);


--
-- Name: model_cards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_cards (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(512) NOT NULL,
    vfolder uuid NOT NULL,
    domain character varying(64) NOT NULL,
    project uuid NOT NULL,
    creator uuid NOT NULL,
    author character varying(256),
    title character varying(512),
    model_version character varying(64),
    description text,
    task character varying(128),
    category character varying(128),
    architecture character varying(128),
    framework character varying[] DEFAULT '{}'::character varying[] NOT NULL,
    label character varying[] DEFAULT '{}'::character varying[] NOT NULL,
    license character varying(128),
    readme text,
    access_level character varying(32) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: networks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.networks (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(128) NOT NULL,
    ref_name character varying(128) NOT NULL,
    driver character varying(64) NOT NULL,
    options jsonb DEFAULT '{}'::jsonb NOT NULL,
    project uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: notification_channels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_channels (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(256) NOT NULL,
    description text,
    channel_type character varying(64) NOT NULL,
    config json NOT NULL,
    enabled boolean NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: notification_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification_rules (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(256) NOT NULL,
    description text,
    rule_type character varying(256) NOT NULL,
    channel_id uuid NOT NULL,
    message_template text NOT NULL,
    enabled boolean NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: object_storages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.object_storages (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying NOT NULL,
    host character varying NOT NULL,
    access_key character varying NOT NULL,
    secret_key character varying NOT NULL,
    endpoint character varying NOT NULL,
    region character varying
);


--
-- Name: organization_auto_generated_file_relations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organization_auto_generated_file_relations (
    organization_type character varying(32) NOT NULL,
    organization_id uuid NOT NULL,
    file_id uuid NOT NULL,
    path text NOT NULL,
    perm text NOT NULL,
    CONSTRAINT ck_organization_auto_generated_file_relations_perm_length CHECK ((char_length(perm) <= 4))
);


--
-- Name: permission_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permission_fields (
    permission_id uuid NOT NULL,
    path text NOT NULL,
    CONSTRAINT ck_permission_fields_path CHECK ((path <> ''::text))
);


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    role_id uuid NOT NULL,
    entity_type character varying(32) NOT NULL,
    permission smallint NOT NULL,
    all_fields boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_permissions_field_scope CHECK ((all_fields OR (permission = ANY (ARRAY[1, 2])))),
    CONSTRAINT ck_permissions_single_bit CHECK (((permission > 0) AND (((permission)::integer & (permission - 1)) = 0)))
);


--
-- Name: preset_resource_slots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.preset_resource_slots (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    preset_id uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    quantity numeric(24,6) NOT NULL
);


--
-- Name: project_fair_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_fair_shares (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    project_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    weight numeric(10,4),
    fair_share_factor numeric(8,6) NOT NULL,
    total_decayed_usage jsonb NOT NULL,
    resource_weights jsonb NOT NULL,
    normalized_usage numeric(8,6) NOT NULL,
    last_calculated_at timestamp with time zone DEFAULT now() NOT NULL,
    lookback_start date DEFAULT CURRENT_DATE NOT NULL,
    lookback_end date DEFAULT CURRENT_DATE NOT NULL,
    half_life_days integer NOT NULL,
    lookback_days integer NOT NULL,
    decay_unit_days integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN project_fair_shares.weight; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.weight IS 'Priority weight multiplier. Higher weight = higher priority allocation ratio. Example: 2.0 means 2x priority compared to default 1.0. NULL means use resource group''s default_weight.';


--
-- Name: COLUMN project_fair_shares.fair_share_factor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.fair_share_factor IS 'Calculated priority score from 0.0 to 1.0. Higher value = less past usage = higher scheduling priority. Formula: F = 2^(-normalized_usage / weight)';


--
-- Name: COLUMN project_fair_shares.total_decayed_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.total_decayed_usage IS 'Sum of historical resource usage with time decay applied. Unit: resource-seconds.';


--
-- Name: COLUMN project_fair_shares.resource_weights; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.resource_weights IS 'Resource weights used in fair share calculation. From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}';


--
-- Name: COLUMN project_fair_shares.normalized_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.normalized_usage IS 'Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). Both usage and capacity are in resource-seconds. Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])';


--
-- Name: COLUMN project_fair_shares.last_calculated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.last_calculated_at IS 'Timestamp when fair_share_factor was last recalculated.';


--
-- Name: COLUMN project_fair_shares.lookback_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.lookback_start IS 'Start date of the usage history window used in last calculation.';


--
-- Name: COLUMN project_fair_shares.lookback_end; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.lookback_end IS 'End date of the usage history window used in last calculation.';


--
-- Name: COLUMN project_fair_shares.half_life_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.half_life_days IS 'Number of days for usage to decay to 50%%.';


--
-- Name: COLUMN project_fair_shares.lookback_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.lookback_days IS 'Number of days of usage history to consider.';


--
-- Name: COLUMN project_fair_shares.decay_unit_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_fair_shares.decay_unit_days IS 'Aggregation period for usage buckets in days.';


--
-- Name: project_resource_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_resource_policies (
    name character varying(256) NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    max_vfolder_count integer NOT NULL,
    max_quota_scope_size bigint NOT NULL,
    max_network_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: project_usage_buckets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_usage_buckets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    project_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    decay_unit_days integer NOT NULL,
    resource_usage jsonb NOT NULL,
    capacity_snapshot jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN project_usage_buckets.capacity_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_usage_buckets.capacity_snapshot IS 'Scaling group capacity at bucket period. Sum of agent.available_slots for calculating usage ratio.';


--
-- Name: prometheus_query_preset_categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prometheus_query_preset_categories (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: prometheus_query_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.prometheus_query_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(256) NOT NULL,
    metric_name character varying(256) NOT NULL,
    query_template text NOT NULL,
    time_window character varying(32),
    description text,
    rank integer DEFAULT 0 NOT NULL,
    category_id uuid,
    options jsonb DEFAULT '{"group_labels": [], "filter_labels": []}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: replica_group_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.replica_group_history (
    replica_group_id uuid NOT NULL,
    deployment_id uuid NOT NULL,
    category character varying(64) DEFAULT 'lifecycle'::character varying NOT NULL,
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    phase character varying(64) NOT NULL,
    from_status character varying(64),
    to_status character varying(64),
    result character varying(32) NOT NULL,
    error_code character varying(128),
    message text NOT NULL,
    sub_steps jsonb DEFAULT '[]'::jsonb NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: replica_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.replica_groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    deployment_id uuid NOT NULL,
    current_revision_id uuid,
    target_revision_id uuid,
    desired_current_replica_count integer DEFAULT 0 NOT NULL,
    desired_target_replica_count integer DEFAULT 0 NOT NULL,
    traffic_weight integer DEFAULT 100 NOT NULL,
    session_group_id uuid NOT NULL,
    lifecycle character varying(64) DEFAULT 'stable'::character varying NOT NULL,
    scaling_status character varying(64) DEFAULT 'stable'::character varying NOT NULL,
    rollout jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: reservoir_registries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reservoir_registries (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    endpoint character varying NOT NULL,
    access_key character varying NOT NULL,
    secret_key character varying NOT NULL,
    api_version character varying NOT NULL
);


--
-- Name: resource_allocations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_allocations (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    kernel_id uuid NOT NULL,
    slot_name character varying(64) NOT NULL,
    requested numeric(24,6) NOT NULL,
    prereserved numeric(24,6) DEFAULT 0 NOT NULL,
    reserved numeric(24,6) DEFAULT 0 NOT NULL,
    used numeric(24,6),
    prereserved_at timestamp with time zone,
    reserved_at timestamp with time zone,
    used_at timestamp with time zone,
    free_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resource_group_volume_offers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_group_volume_offers (
    resource_group_id uuid NOT NULL,
    storage_volume_id uuid NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: resource_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(256) NOT NULL,
    resource_slots jsonb NOT NULL,
    shared_memory bigint,
    scaling_group_name character varying(64) DEFAULT NULL::character varying
);


--
-- Name: resource_slot_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_slot_types (
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    slot_name character varying(64) NOT NULL,
    slot_type character varying(16) NOT NULL,
    required boolean DEFAULT false NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    display_name character varying(128) DEFAULT ''::character varying NOT NULL,
    description character varying(256) DEFAULT ''::character varying NOT NULL,
    display_unit character varying(32) DEFAULT ''::character varying NOT NULL,
    display_icon character varying(64) DEFAULT ''::character varying NOT NULL,
    number_format jsonb DEFAULT '{"binary": false, "round_length": 0}'::jsonb NOT NULL,
    rank integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: retention_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.retention_policies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    category character varying(64) NOT NULL,
    retention_period interval NOT NULL,
    enabled boolean DEFAULT false NOT NULL,
    last_swept_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: role_permission_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permission_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    role_preset_id uuid NOT NULL,
    entity_type character varying(32) NOT NULL,
    permission smallint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: role_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    role_name_template text,
    scope_type character varying(32) NOT NULL,
    scope_id uuid,
    auto_assign boolean DEFAULT false NOT NULL,
    auto_assign_to_owner boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    description text,
    source character varying(16) DEFAULT 'system'::character varying NOT NULL,
    status character varying(64) DEFAULT 'active'::character varying NOT NULL,
    auto_assign boolean DEFAULT false NOT NULL,
    deleted_at timestamp with time zone,
    scope_type character varying(32) NOT NULL,
    scope_id uuid NOT NULL,
    role_preset_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: route_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.route_history (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    route_id uuid NOT NULL,
    deployment_id uuid NOT NULL,
    category character varying(64) DEFAULT 'lifecycle'::character varying NOT NULL,
    phase character varying(64) NOT NULL,
    from_status character varying(64),
    to_status character varying(64),
    from_sub_status character varying(64),
    to_sub_status character varying(64),
    result character varying(32) NOT NULL,
    error_code character varying(128),
    message text NOT NULL,
    sub_steps jsonb DEFAULT '[]'::jsonb NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: routings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.routings (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    endpoint uuid NOT NULL,
    session uuid,
    session_owner uuid NOT NULL,
    domain character varying(64) NOT NULL,
    project uuid NOT NULL,
    status character varying(64) NOT NULL,
    health_status character varying(64) DEFAULT 'not_checked'::character varying NOT NULL,
    weight integer,
    traffic_ratio double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    error_data jsonb,
    replica_host character varying(256),
    replica_port integer,
    health_check jsonb,
    termination_grace_period double precision DEFAULT '30'::double precision NOT NULL,
    revision uuid NOT NULL,
    replica_group_id uuid,
    traffic_status character varying(64) DEFAULT 'inactive'::character varying NOT NULL,
    sub_status character varying(64) DEFAULT 'pending'::character varying,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: runtime_variant_presets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.runtime_variant_presets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    runtime_variant uuid NOT NULL,
    name character varying(256) NOT NULL,
    description text,
    rank integer NOT NULL,
    preset_target character varying(16) NOT NULL,
    value_type character varying(16) NOT NULL,
    default_value character varying(512),
    key character varying(256) NOT NULL,
    required boolean DEFAULT false NOT NULL,
    added_version text,
    deprecated_version text,
    added_version_major integer GENERATED ALWAYS AS (
CASE
    WHEN (added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(added_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[1]
    ELSE NULL::integer
END) STORED,
    added_version_minor integer GENERATED ALWAYS AS (
CASE
    WHEN (added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(added_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[2]
    ELSE NULL::integer
END) STORED,
    added_version_patch integer GENERATED ALWAYS AS (
CASE
    WHEN (added_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(added_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[3]
    ELSE NULL::integer
END) STORED,
    deprecated_version_major integer GENERATED ALWAYS AS (
CASE
    WHEN (deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(deprecated_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[1]
    ELSE NULL::integer
END) STORED,
    deprecated_version_minor integer GENERATED ALWAYS AS (
CASE
    WHEN (deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(deprecated_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[2]
    ELSE NULL::integer
END) STORED,
    deprecated_version_patch integer GENERATED ALWAYS AS (
CASE
    WHEN (deprecated_version ~ '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text) THEN (((string_to_array("substring"(deprecated_version, '^[0-9]{1,9}(?![0-9])(?:[.][0-9]{1,9}(?![0-9])){0,2}'::text), '.'::text))::integer[] || ARRAY[0, 0, 0]))[3]
    ELSE NULL::integer
END) STORED,
    category character varying(64),
    display_name character varying(256),
    ui_option jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: runtime_variants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.runtime_variants (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(128) NOT NULL,
    description text,
    reads_vfolder_config_files boolean DEFAULT false NOT NULL,
    default_model_definition jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scaling_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scaling_groups (
    name character varying(64) NOT NULL,
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    description character varying(512),
    is_active boolean,
    is_public boolean DEFAULT true NOT NULL,
    is_default boolean DEFAULT false NOT NULL,
    wsproxy_addr character varying(1024),
    wsproxy_api_token character varying(128),
    driver character varying(64) NOT NULL,
    driver_opts jsonb NOT NULL,
    scheduler character varying(64) NOT NULL,
    use_host_network boolean NOT NULL,
    scheduler_opts jsonb NOT NULL,
    fair_share_spec jsonb,
    default_deployment_options jsonb NOT NULL,
    default_session_options jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: scope_bindings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scope_bindings (
    virtual_entity_id uuid NOT NULL,
    scope_entity_id uuid NOT NULL,
    permission_cap smallint,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: service_catalog; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_catalog (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    service_group character varying(64) NOT NULL,
    instance_id character varying(128) NOT NULL,
    display_name character varying(256) NOT NULL,
    version character varying(64) NOT NULL,
    labels jsonb DEFAULT '{}'::jsonb NOT NULL,
    status character varying(64) NOT NULL,
    startup_time timestamp with time zone NOT NULL,
    registered_at timestamp with time zone DEFAULT now() NOT NULL,
    last_heartbeat timestamp with time zone DEFAULT now() NOT NULL,
    config_hash character varying(128) DEFAULT ''::character varying NOT NULL
);


--
-- Name: service_catalog_endpoint; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_catalog_endpoint (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    service_id uuid NOT NULL,
    role character varying(32) NOT NULL,
    scope character varying(32) NOT NULL,
    address character varying(256) NOT NULL,
    port integer NOT NULL,
    protocol character varying(16) NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb
);


--
-- Name: service_storage_backend_status; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.service_storage_backend_status (
    service_catalog_id uuid NOT NULL,
    storage_backend_id uuid NOT NULL,
    status_checked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: session_dependencies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_dependencies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_id uuid NOT NULL,
    depends_on uuid NOT NULL
);


--
-- Name: session_designated_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_designated_agents (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_id uuid NOT NULL,
    agent_uuid uuid NOT NULL
);


--
-- Name: session_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    domain_id uuid NOT NULL,
    project_id uuid NOT NULL,
    owner_user_id uuid NOT NULL,
    placement_direction character varying(64) NOT NULL,
    placement_enforcement character varying(64) NOT NULL,
    deleted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: session_idle_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_idle_checks (
    session_id uuid NOT NULL,
    idle_checker_id uuid NOT NULL,
    expire_at timestamp with time zone,
    last_status character varying(64) NOT NULL,
    last_message text NOT NULL,
    is_manual boolean DEFAULT false NOT NULL,
    manually_triggered_by uuid,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_session_idle_checks_manual_trigger CHECK (((manually_triggered_by IS NULL) OR is_manual))
);


--
-- Name: session_scheduling_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_scheduling_history (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    session_id uuid NOT NULL,
    phase character varying(64) NOT NULL,
    from_status character varying(64),
    to_status character varying(64),
    result character varying(32) NOT NULL,
    error_code character varying(128),
    message text NOT NULL,
    sub_steps jsonb DEFAULT '[]'::jsonb NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: session_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.session_templates (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    is_active boolean,
    domain_name character varying(64) NOT NULL,
    group_id uuid,
    user_uuid uuid NOT NULL,
    type public.templatetype DEFAULT 'TASK'::public.templatetype NOT NULL,
    name character varying(128),
    template jsonb NOT NULL
);


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    creation_id character varying(32),
    name character varying(128),
    session_type character varying(64) DEFAULT 'INTERACTIVE'::character varying NOT NULL,
    priority integer NOT NULL,
    is_preemptible boolean DEFAULT true NOT NULL,
    job_priority integer DEFAULT 0 NOT NULL,
    cluster_mode character varying(16) DEFAULT 'SINGLE_NODE'::character varying NOT NULL,
    cluster_size integer NOT NULL,
    options jsonb NOT NULL,
    agent_ids character varying[],
    session_group_id uuid,
    resource_group_id uuid NOT NULL,
    scaling_group_name character varying(64) NOT NULL,
    target_sgroup_names character varying(64)[] DEFAULT '{}'::character varying[],
    domain_name character varying(64) NOT NULL,
    domain_id uuid NOT NULL,
    group_id uuid NOT NULL,
    user_uuid uuid,
    access_key character varying(20),
    images character varying[],
    image_ids uuid[],
    tag character varying(64),
    vfolder_mounts jsonb,
    environ jsonb,
    bootstrap_script character varying(16384),
    use_host_network boolean NOT NULL,
    timeout bigint,
    batch_timeout bigint,
    terminated_at timestamp with time zone,
    starts_at timestamp with time zone,
    requested_starts_at timestamp with time zone,
    status character varying(64) DEFAULT 'PENDING'::character varying NOT NULL,
    status_info character varying,
    status_data jsonb,
    status_history jsonb,
    callback_url text,
    startup_command text,
    result character varying(64) DEFAULT 'UNDEFINED'::character varying NOT NULL,
    num_queries bigint,
    last_stat jsonb,
    network_type character varying(64),
    network_id character varying(128),
    replica_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: sgroups_for_domains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sgroups_for_domains (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group_id uuid NOT NULL,
    domain_id uuid NOT NULL
);


--
-- Name: sgroups_for_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sgroups_for_groups (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group_id uuid NOT NULL,
    "group" uuid NOT NULL
);


--
-- Name: sgroups_for_keypairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sgroups_for_keypairs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group_id uuid NOT NULL,
    access_key character varying(20) NOT NULL
);


--
-- Name: ssh_keypairs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ssh_keypairs (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    user_id uuid NOT NULL,
    public_key text NOT NULL,
    private_key text,
    is_default boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: storage_backend_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage_backend_types (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    capabilities jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: storage_backends; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage_backends (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    storage_backend_type_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: storage_namespace; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage_namespace (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    storage_id uuid NOT NULL,
    namespace character varying NOT NULL
);


--
-- Name: storage_volume_service_holdings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage_volume_service_holdings (
    service_catalog_id uuid NOT NULL,
    storage_volume_id uuid NOT NULL,
    status character varying(64) NOT NULL,
    status_checked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: storage_volumes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.storage_volumes (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying(64) NOT NULL,
    storage_backend_id uuid NOT NULL,
    status_stale_after interval DEFAULT '01:00:00'::interval NOT NULL,
    usage_exposure jsonb DEFAULT '{"exposed": ["percentage"]}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: system_session_environ; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_session_environ (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    value_source character varying(64) NOT NULL,
    key character varying(256) NOT NULL,
    scope_type character varying(64) NOT NULL,
    scope_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    CONSTRAINT ck_system_session_environ_key_is_environ_name CHECK (((key)::text ~ '^[A-Za-z_][A-Za-z0-9_]*$'::text))
);


--
-- Name: usage_bucket_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usage_bucket_entries (
    bucket_id uuid NOT NULL,
    bucket_type character varying(16) NOT NULL,
    slot_name character varying(64) NOT NULL,
    resource_usage numeric NOT NULL,
    capacity numeric(24,6) NOT NULL
);


--
-- Name: user_default_bootstrap_scripts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_default_bootstrap_scripts (
    user_id uuid NOT NULL,
    script_id uuid NOT NULL
);


--
-- Name: user_fair_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_fair_shares (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    user_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    weight numeric(10,4),
    fair_share_factor numeric(8,6) NOT NULL,
    scheduling_rank integer,
    total_decayed_usage jsonb NOT NULL,
    resource_weights jsonb NOT NULL,
    normalized_usage numeric(8,6) NOT NULL,
    last_calculated_at timestamp with time zone DEFAULT now() NOT NULL,
    lookback_start date DEFAULT CURRENT_DATE NOT NULL,
    lookback_end date DEFAULT CURRENT_DATE NOT NULL,
    half_life_days integer NOT NULL,
    lookback_days integer NOT NULL,
    decay_unit_days integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN user_fair_shares.weight; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.weight IS 'Priority weight multiplier. Higher weight = higher priority allocation ratio. Example: 2.0 means 2x priority compared to default 1.0. NULL means use resource group''s default_weight.';


--
-- Name: COLUMN user_fair_shares.fair_share_factor; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.fair_share_factor IS 'Calculated priority score from 0.0 to 1.0. Higher value = less past usage = higher scheduling priority. Formula: F = 2^(-normalized_usage / weight)';


--
-- Name: COLUMN user_fair_shares.scheduling_rank; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.scheduling_rank IS 'Computed scheduling priority rank. Lower value = higher priority (1 = highest). NULL means rank calculation has not been performed yet.';


--
-- Name: COLUMN user_fair_shares.total_decayed_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.total_decayed_usage IS 'Sum of historical resource usage with time decay applied. Unit: resource-seconds.';


--
-- Name: COLUMN user_fair_shares.resource_weights; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.resource_weights IS 'Resource weights used in fair share calculation. From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}';


--
-- Name: COLUMN user_fair_shares.normalized_usage; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.normalized_usage IS 'Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). Both usage and capacity are in resource-seconds. Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])';


--
-- Name: COLUMN user_fair_shares.last_calculated_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.last_calculated_at IS 'Timestamp when fair_share_factor was last recalculated.';


--
-- Name: COLUMN user_fair_shares.lookback_start; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.lookback_start IS 'Start date of the usage history window used in last calculation.';


--
-- Name: COLUMN user_fair_shares.lookback_end; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.lookback_end IS 'End date of the usage history window used in last calculation.';


--
-- Name: COLUMN user_fair_shares.half_life_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.half_life_days IS 'Number of days for usage to decay to 50%%.';


--
-- Name: COLUMN user_fair_shares.lookback_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.lookback_days IS 'Number of days of usage history to consider.';


--
-- Name: COLUMN user_fair_shares.decay_unit_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_fair_shares.decay_unit_days IS 'Aggregation period for usage buckets in days.';


--
-- Name: user_resource_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_resource_policies (
    name character varying(256) NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    max_vfolder_count integer NOT NULL,
    max_quota_scope_size bigint NOT NULL,
    max_session_count_per_model_session integer NOT NULL,
    max_customized_image_count integer NOT NULL,
    max_concurrent_logins integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    granted_by uuid,
    granted_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_usage_buckets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_usage_buckets (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    user_uuid uuid NOT NULL,
    project_id uuid NOT NULL,
    domain_name character varying(64) NOT NULL,
    resource_group character varying(64) NOT NULL,
    resource_group_id uuid NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    decay_unit_days integer NOT NULL,
    resource_usage jsonb NOT NULL,
    capacity_snapshot jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: COLUMN user_usage_buckets.capacity_snapshot; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.user_usage_buckets.capacity_snapshot IS 'Scaling group capacity at bucket period. Sum of agent.available_slots for calculating usage ratio.';


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    uuid uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(64) NOT NULL,
    password character varying,
    need_password_change boolean DEFAULT false NOT NULL,
    password_changed_at timestamp with time zone DEFAULT now() NOT NULL,
    full_name character varying(64),
    description character varying(500),
    status public.userstatus NOT NULL,
    status_info character varying,
    integration_id character varying(512),
    domain_name character varying(64) NOT NULL,
    domain_id uuid NOT NULL,
    role public.userrole NOT NULL,
    allowed_client_ip cidr[],
    totp_key character varying(32),
    totp_activated boolean DEFAULT false NOT NULL,
    totp_activated_at timestamp with time zone,
    resource_policy character varying(256) NOT NULL,
    sudo_session_enabled boolean NOT NULL,
    container_uid integer,
    container_main_gid integer,
    container_gids integer[],
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: vfolder_attachment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vfolder_attachment (
    vfolder uuid NOT NULL,
    kernel uuid NOT NULL
);


--
-- Name: vfolder_auto_mounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vfolder_auto_mounts (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    scope_type character varying(32) NOT NULL,
    scope_id uuid NOT NULL,
    vfolder_id uuid NOT NULL,
    mount_destination text NOT NULL,
    subpath text DEFAULT '.'::text NOT NULL,
    mount_permission character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone
);


--
-- Name: vfolder_user_mount_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vfolder_user_mount_policies (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    vfolder_id uuid NOT NULL,
    user_id uuid NOT NULL,
    permission character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: vfolders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vfolders (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    host character varying(128) NOT NULL,
    storage_volume_id uuid,
    domain_name character varying(64) NOT NULL,
    quota_scope_id character varying(64) NOT NULL,
    name character varying(128) NOT NULL,
    usage_mode public.vfolderusagemode NOT NULL,
    default_mount_permission character varying(64) NOT NULL,
    max_files integer,
    max_size integer,
    num_files integer,
    cur_size integer,
    last_used timestamp with time zone,
    creator character varying(128),
    creator_id uuid,
    unmanaged_path character varying(512),
    ownership_type public.vfolderownershiptype NOT NULL,
    "user" uuid,
    "group" uuid,
    cloneable boolean NOT NULL,
    status character varying(64) DEFAULT 'ready'::character varying NOT NULL,
    status_history jsonb,
    status_changed timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: vfs_storages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vfs_storages (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    name character varying NOT NULL,
    host character varying NOT NULL,
    base_path character varying NOT NULL
);


--
-- Name: virtual_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.virtual_entities (
    id uuid DEFAULT public.uuid_generate_v7() NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: agent_installed_images pk_agent_installed_images; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_installed_images
    ADD CONSTRAINT pk_agent_installed_images PRIMARY KEY (agent_id, image_id);


--
-- Name: agent_resources pk_agent_resources; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_resources
    ADD CONSTRAINT pk_agent_resources PRIMARY KEY (agent_id, slot_name);


--
-- Name: agents pk_agents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT pk_agents PRIMARY KEY (id);


--
-- Name: app_config_allow_list pk_app_config_allow_list; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_allow_list
    ADD CONSTRAINT pk_app_config_allow_list PRIMARY KEY (id);


--
-- Name: app_config_definitions pk_app_config_definitions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_definitions
    ADD CONSTRAINT pk_app_config_definitions PRIMARY KEY (id);


--
-- Name: app_config_fragments pk_app_config_fragments; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_fragments
    ADD CONSTRAINT pk_app_config_fragments PRIMARY KEY (id);


--
-- Name: artifact_registries pk_artifact_registries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_registries
    ADD CONSTRAINT pk_artifact_registries PRIMARY KEY (id);


--
-- Name: artifact_revisions pk_artifact_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_revisions
    ADD CONSTRAINT pk_artifact_revisions PRIMARY KEY (id);


--
-- Name: artifacts pk_artifacts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT pk_artifacts PRIMARY KEY (id);


--
-- Name: association_artifacts_storages pk_association_artifacts_storages; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_artifacts_storages
    ADD CONSTRAINT pk_association_artifacts_storages PRIMARY KEY (id);


--
-- Name: association_container_registries_groups pk_association_container_registries_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_container_registries_groups
    ADD CONSTRAINT pk_association_container_registries_groups PRIMARY KEY (id);


--
-- Name: association_groups_users pk_association_groups_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_groups_users
    ADD CONSTRAINT pk_association_groups_users PRIMARY KEY (id);


--
-- Name: audit_log_scopes pk_audit_log_scopes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log_scopes
    ADD CONSTRAINT pk_audit_log_scopes PRIMARY KEY (id);


--
-- Name: audit_logs pk_audit_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT pk_audit_logs PRIMARY KEY (id);


--
-- Name: auto_generated_file_revisions pk_auto_generated_file_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_file_revisions
    ADD CONSTRAINT pk_auto_generated_file_revisions PRIMARY KEY (id);


--
-- Name: auto_generated_files pk_auto_generated_files; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_files
    ADD CONSTRAINT pk_auto_generated_files PRIMARY KEY (id);


--
-- Name: bootstrap_script_revisions pk_bootstrap_script_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bootstrap_script_revisions
    ADD CONSTRAINT pk_bootstrap_script_revisions PRIMARY KEY (id);


--
-- Name: bootstrap_scripts pk_bootstrap_scripts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bootstrap_scripts
    ADD CONSTRAINT pk_bootstrap_scripts PRIMARY KEY (id);


--
-- Name: client_ip_masking_policies pk_client_ip_masking_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_ip_masking_policies
    ADD CONSTRAINT pk_client_ip_masking_policies PRIMARY KEY (id);


--
-- Name: container_registries pk_container_registries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.container_registries
    ADD CONSTRAINT pk_container_registries PRIMARY KEY (id);


--
-- Name: deployment_auto_scaling_policies pk_deployment_auto_scaling_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_auto_scaling_policies
    ADD CONSTRAINT pk_deployment_auto_scaling_policies PRIMARY KEY (id);


--
-- Name: deployment_designated_agents pk_deployment_designated_agents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_designated_agents
    ADD CONSTRAINT pk_deployment_designated_agents PRIMARY KEY (endpoint_id, agent_uuid);


--
-- Name: deployment_history pk_deployment_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_history
    ADD CONSTRAINT pk_deployment_history PRIMARY KEY (id);


--
-- Name: deployment_policies pk_deployment_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_policies
    ADD CONSTRAINT pk_deployment_policies PRIMARY KEY (id);


--
-- Name: deployment_revision_presets pk_deployment_revision_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_presets
    ADD CONSTRAINT pk_deployment_revision_presets PRIMARY KEY (id);


--
-- Name: deployment_revision_resource_slots pk_deployment_revision_resource_slots; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_resource_slots
    ADD CONSTRAINT pk_deployment_revision_resource_slots PRIMARY KEY (revision_id, slot_name);


--
-- Name: deployment_revisions pk_deployment_revisions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT pk_deployment_revisions PRIMARY KEY (id);


--
-- Name: domain_container_registry_relations pk_domain_container_registry_relations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_container_registry_relations
    ADD CONSTRAINT pk_domain_container_registry_relations PRIMARY KEY (domain_id, container_registry_id);


--
-- Name: domain_fair_shares pk_domain_fair_shares; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_fair_shares
    ADD CONSTRAINT pk_domain_fair_shares PRIMARY KEY (id);


--
-- Name: domain_usage_buckets pk_domain_usage_buckets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_usage_buckets
    ADD CONSTRAINT pk_domain_usage_buckets PRIMARY KEY (id);


--
-- Name: domains pk_domains; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domains
    ADD CONSTRAINT pk_domains PRIMARY KEY (name);


--
-- Name: endpoint_auto_scaling_rules pk_endpoint_auto_scaling_rules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_auto_scaling_rules
    ADD CONSTRAINT pk_endpoint_auto_scaling_rules PRIMARY KEY (id);


--
-- Name: endpoint_tokens pk_endpoint_tokens; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_tokens
    ADD CONSTRAINT pk_endpoint_tokens PRIMARY KEY (id);


--
-- Name: endpoints pk_endpoints; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT pk_endpoints PRIMARY KEY (id);


--
-- Name: entity_fields pk_entity_fields; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_fields
    ADD CONSTRAINT pk_entity_fields PRIMARY KEY (id);


--
-- Name: entity_labels pk_entity_labels; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_labels
    ADD CONSTRAINT pk_entity_labels PRIMARY KEY (id);


--
-- Name: entity_membership_caps pk_entity_membership_caps; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_membership_caps
    ADD CONSTRAINT pk_entity_membership_caps PRIMARY KEY (id);


--
-- Name: entity_membership_fields pk_entity_membership_fields; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_membership_fields
    ADD CONSTRAINT pk_entity_membership_fields PRIMARY KEY (cap_id, path);


--
-- Name: entity_memberships pk_entity_memberships; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_memberships
    ADD CONSTRAINT pk_entity_memberships PRIMARY KEY (id);


--
-- Name: entity_shares pk_entity_shares; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_shares
    ADD CONSTRAINT pk_entity_shares PRIMARY KEY (id);


--
-- Name: error_logs pk_error_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.error_logs
    ADD CONSTRAINT pk_error_logs PRIMARY KEY (id);


--
-- Name: event_logs pk_event_logs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_logs
    ADD CONSTRAINT pk_event_logs PRIMARY KEY (id);


--
-- Name: global_entities pk_global_entities; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.global_entities
    ADD CONSTRAINT pk_global_entities PRIMARY KEY (id);


--
-- Name: groups pk_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT pk_groups PRIMARY KEY (id);


--
-- Name: huggingface_registries pk_huggingface_registries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.huggingface_registries
    ADD CONSTRAINT pk_huggingface_registries PRIMARY KEY (id);


--
-- Name: idle_checker_bindings pk_idle_checker_bindings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idle_checker_bindings
    ADD CONSTRAINT pk_idle_checker_bindings PRIMARY KEY (id);


--
-- Name: idle_checkers pk_idle_checkers; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idle_checkers
    ADD CONSTRAINT pk_idle_checkers PRIMARY KEY (id);


--
-- Name: image_aliases pk_image_aliases; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_aliases
    ADD CONSTRAINT pk_image_aliases PRIMARY KEY (id);


--
-- Name: images pk_images; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.images
    ADD CONSTRAINT pk_images PRIMARY KEY (id);


--
-- Name: kernel_group_environ pk_kernel_group_environ; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_environ
    ADD CONSTRAINT pk_kernel_group_environ PRIMARY KEY (id);


--
-- Name: kernel_group_resource_slots pk_kernel_group_resource_slots; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_resource_slots
    ADD CONSTRAINT pk_kernel_group_resource_slots PRIMARY KEY (id);


--
-- Name: kernel_group_vfolder_mounts pk_kernel_group_vfolder_mounts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_vfolder_mounts
    ADD CONSTRAINT pk_kernel_group_vfolder_mounts PRIMARY KEY (id);


--
-- Name: kernel_groups pk_kernel_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_groups
    ADD CONSTRAINT pk_kernel_groups PRIMARY KEY (id);


--
-- Name: kernel_scheduling_history pk_kernel_scheduling_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_scheduling_history
    ADD CONSTRAINT pk_kernel_scheduling_history PRIMARY KEY (id);


--
-- Name: kernel_usage_records pk_kernel_usage_records; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_usage_records
    ADD CONSTRAINT pk_kernel_usage_records PRIMARY KEY (id);


--
-- Name: kernels pk_kernels; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT pk_kernels PRIMARY KEY (id);


--
-- Name: keypair_resource_policies pk_keypair_resource_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypair_resource_policies
    ADD CONSTRAINT pk_keypair_resource_policies PRIMARY KEY (name);


--
-- Name: keypairs pk_keypairs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypairs
    ADD CONSTRAINT pk_keypairs PRIMARY KEY (access_key);


--
-- Name: login_client_types pk_login_client_types; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_client_types
    ADD CONSTRAINT pk_login_client_types PRIMARY KEY (id);


--
-- Name: login_history pk_login_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT pk_login_history PRIMARY KEY (id);


--
-- Name: login_sessions pk_login_sessions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_sessions
    ADD CONSTRAINT pk_login_sessions PRIMARY KEY (id);


--
-- Name: model_card_resource_requirements pk_model_card_resource_requirements; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_card_resource_requirements
    ADD CONSTRAINT pk_model_card_resource_requirements PRIMARY KEY (model_card_id, slot_name);


--
-- Name: model_cards pk_model_cards; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT pk_model_cards PRIMARY KEY (id);


--
-- Name: networks pk_networks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.networks
    ADD CONSTRAINT pk_networks PRIMARY KEY (id);


--
-- Name: notification_channels pk_notification_channels; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_channels
    ADD CONSTRAINT pk_notification_channels PRIMARY KEY (id);


--
-- Name: notification_rules pk_notification_rules; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification_rules
    ADD CONSTRAINT pk_notification_rules PRIMARY KEY (id);


--
-- Name: object_storages pk_object_storages; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.object_storages
    ADD CONSTRAINT pk_object_storages PRIMARY KEY (id);


--
-- Name: organization_auto_generated_file_relations pk_organization_auto_generated_file_relations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_auto_generated_file_relations
    ADD CONSTRAINT pk_organization_auto_generated_file_relations PRIMARY KEY (organization_type, organization_id, file_id);


--
-- Name: permission_fields pk_permission_fields; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_fields
    ADD CONSTRAINT pk_permission_fields PRIMARY KEY (permission_id, path);


--
-- Name: permissions pk_permissions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT pk_permissions PRIMARY KEY (id);


--
-- Name: preset_resource_slots pk_preset_resource_slots; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preset_resource_slots
    ADD CONSTRAINT pk_preset_resource_slots PRIMARY KEY (preset_id, slot_name);


--
-- Name: project_fair_shares pk_project_fair_shares; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_fair_shares
    ADD CONSTRAINT pk_project_fair_shares PRIMARY KEY (id);


--
-- Name: project_resource_policies pk_project_resource_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_resource_policies
    ADD CONSTRAINT pk_project_resource_policies PRIMARY KEY (name);


--
-- Name: project_usage_buckets pk_project_usage_buckets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_usage_buckets
    ADD CONSTRAINT pk_project_usage_buckets PRIMARY KEY (id);


--
-- Name: prometheus_query_preset_categories pk_prometheus_query_preset_categories; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prometheus_query_preset_categories
    ADD CONSTRAINT pk_prometheus_query_preset_categories PRIMARY KEY (id);


--
-- Name: prometheus_query_presets pk_prometheus_query_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prometheus_query_presets
    ADD CONSTRAINT pk_prometheus_query_presets PRIMARY KEY (id);


--
-- Name: replica_group_history pk_replica_group_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replica_group_history
    ADD CONSTRAINT pk_replica_group_history PRIMARY KEY (id);


--
-- Name: replica_groups pk_replica_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replica_groups
    ADD CONSTRAINT pk_replica_groups PRIMARY KEY (id);


--
-- Name: reservoir_registries pk_reservoir_registries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reservoir_registries
    ADD CONSTRAINT pk_reservoir_registries PRIMARY KEY (id);


--
-- Name: resource_allocations pk_resource_allocations; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT pk_resource_allocations PRIMARY KEY (kernel_id, slot_name);


--
-- Name: resource_group_volume_offers pk_resource_group_volume_offers; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_group_volume_offers
    ADD CONSTRAINT pk_resource_group_volume_offers PRIMARY KEY (resource_group_id, storage_volume_id);


--
-- Name: resource_presets pk_resource_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_presets
    ADD CONSTRAINT pk_resource_presets PRIMARY KEY (id);


--
-- Name: resource_slot_types pk_resource_slot_types; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_slot_types
    ADD CONSTRAINT pk_resource_slot_types PRIMARY KEY (slot_name);


--
-- Name: retention_policies pk_retention_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retention_policies
    ADD CONSTRAINT pk_retention_policies PRIMARY KEY (id);


--
-- Name: role_permission_presets pk_role_permission_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission_presets
    ADD CONSTRAINT pk_role_permission_presets PRIMARY KEY (id);


--
-- Name: role_presets pk_role_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_presets
    ADD CONSTRAINT pk_role_presets PRIMARY KEY (id);


--
-- Name: roles pk_roles; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT pk_roles PRIMARY KEY (id);


--
-- Name: route_history pk_route_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.route_history
    ADD CONSTRAINT pk_route_history PRIMARY KEY (id);


--
-- Name: routings pk_routings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT pk_routings PRIMARY KEY (id);


--
-- Name: runtime_variant_presets pk_runtime_variant_presets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_variant_presets
    ADD CONSTRAINT pk_runtime_variant_presets PRIMARY KEY (id);


--
-- Name: runtime_variants pk_runtime_variants; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_variants
    ADD CONSTRAINT pk_runtime_variants PRIMARY KEY (id);


--
-- Name: scaling_groups pk_scaling_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scaling_groups
    ADD CONSTRAINT pk_scaling_groups PRIMARY KEY (name);


--
-- Name: scope_bindings pk_scope_bindings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scope_bindings
    ADD CONSTRAINT pk_scope_bindings PRIMARY KEY (virtual_entity_id, scope_entity_id);


--
-- Name: service_catalog pk_service_catalog; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_catalog
    ADD CONSTRAINT pk_service_catalog PRIMARY KEY (id);


--
-- Name: service_catalog_endpoint pk_service_catalog_endpoint; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_catalog_endpoint
    ADD CONSTRAINT pk_service_catalog_endpoint PRIMARY KEY (id);


--
-- Name: service_storage_backend_status pk_service_storage_backend_status; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_storage_backend_status
    ADD CONSTRAINT pk_service_storage_backend_status PRIMARY KEY (service_catalog_id, storage_backend_id);


--
-- Name: session_designated_agents pk_session_designated_agents; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_designated_agents
    ADD CONSTRAINT pk_session_designated_agents PRIMARY KEY (id);


--
-- Name: session_groups pk_session_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_groups
    ADD CONSTRAINT pk_session_groups PRIMARY KEY (id);


--
-- Name: session_idle_checks pk_session_idle_checks; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_idle_checks
    ADD CONSTRAINT pk_session_idle_checks PRIMARY KEY (session_id, idle_checker_id);


--
-- Name: session_scheduling_history pk_session_scheduling_history; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_scheduling_history
    ADD CONSTRAINT pk_session_scheduling_history PRIMARY KEY (id);


--
-- Name: session_templates pk_session_templates; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_templates
    ADD CONSTRAINT pk_session_templates PRIMARY KEY (id);


--
-- Name: sessions pk_sessions; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT pk_sessions PRIMARY KEY (id);


--
-- Name: sgroups_for_domains pk_sgroups_for_domains; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_domains
    ADD CONSTRAINT pk_sgroups_for_domains PRIMARY KEY (id);


--
-- Name: sgroups_for_groups pk_sgroups_for_groups; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_groups
    ADD CONSTRAINT pk_sgroups_for_groups PRIMARY KEY (id);


--
-- Name: sgroups_for_keypairs pk_sgroups_for_keypairs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_keypairs
    ADD CONSTRAINT pk_sgroups_for_keypairs PRIMARY KEY (id);


--
-- Name: ssh_keypairs pk_ssh_keypairs; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssh_keypairs
    ADD CONSTRAINT pk_ssh_keypairs PRIMARY KEY (id);


--
-- Name: storage_backend_types pk_storage_backend_types; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_backend_types
    ADD CONSTRAINT pk_storage_backend_types PRIMARY KEY (id);


--
-- Name: storage_backends pk_storage_backends; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_backends
    ADD CONSTRAINT pk_storage_backends PRIMARY KEY (id);


--
-- Name: storage_namespace pk_storage_namespace; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_namespace
    ADD CONSTRAINT pk_storage_namespace PRIMARY KEY (id);


--
-- Name: storage_volume_service_holdings pk_storage_volume_service_holdings; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volume_service_holdings
    ADD CONSTRAINT pk_storage_volume_service_holdings PRIMARY KEY (service_catalog_id, storage_volume_id);


--
-- Name: storage_volumes pk_storage_volumes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volumes
    ADD CONSTRAINT pk_storage_volumes PRIMARY KEY (id);


--
-- Name: system_session_environ pk_system_session_environ; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_session_environ
    ADD CONSTRAINT pk_system_session_environ PRIMARY KEY (id);


--
-- Name: usage_bucket_entries pk_usage_bucket_entries; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usage_bucket_entries
    ADD CONSTRAINT pk_usage_bucket_entries PRIMARY KEY (bucket_id, slot_name);


--
-- Name: user_default_bootstrap_scripts pk_user_default_bootstrap_scripts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_default_bootstrap_scripts
    ADD CONSTRAINT pk_user_default_bootstrap_scripts PRIMARY KEY (user_id);


--
-- Name: user_fair_shares pk_user_fair_shares; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fair_shares
    ADD CONSTRAINT pk_user_fair_shares PRIMARY KEY (id);


--
-- Name: user_resource_policies pk_user_resource_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_resource_policies
    ADD CONSTRAINT pk_user_resource_policies PRIMARY KEY (name);


--
-- Name: user_roles pk_user_roles; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT pk_user_roles PRIMARY KEY (id);


--
-- Name: user_usage_buckets pk_user_usage_buckets; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage_buckets
    ADD CONSTRAINT pk_user_usage_buckets PRIMARY KEY (id);


--
-- Name: users pk_users; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT pk_users PRIMARY KEY (uuid);


--
-- Name: vfolder_attachment pk_vfolder_attachment; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_attachment
    ADD CONSTRAINT pk_vfolder_attachment PRIMARY KEY (vfolder, kernel);


--
-- Name: vfolder_auto_mounts pk_vfolder_auto_mounts; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_auto_mounts
    ADD CONSTRAINT pk_vfolder_auto_mounts PRIMARY KEY (id);


--
-- Name: vfolder_user_mount_policies pk_vfolder_user_mount_policies; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_user_mount_policies
    ADD CONSTRAINT pk_vfolder_user_mount_policies PRIMARY KEY (id);


--
-- Name: vfolders pk_vfolders; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolders
    ADD CONSTRAINT pk_vfolders PRIMARY KEY (id);


--
-- Name: vfs_storages pk_vfs_storages; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfs_storages
    ADD CONSTRAINT pk_vfs_storages PRIMARY KEY (id);


--
-- Name: virtual_entities pk_virtual_entities; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.virtual_entities
    ADD CONSTRAINT pk_virtual_entities PRIMARY KEY (id);


--
-- Name: session_dependencies sess_dep_pk; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_dependencies
    ADD CONSTRAINT sess_dep_pk PRIMARY KEY (session_id, depends_on);


--
-- Name: agent_resources uq_agent_resources_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_resources
    ADD CONSTRAINT uq_agent_resources_id UNIQUE (id);


--
-- Name: agents uq_agents_uuid; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT uq_agents_uuid UNIQUE (uuid);


--
-- Name: app_config_allow_list uq_app_config_allow_list_config_name_scope_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_allow_list
    ADD CONSTRAINT uq_app_config_allow_list_config_name_scope_type UNIQUE (config_name, scope_type);


--
-- Name: app_config_definitions uq_app_config_definitions_config_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_definitions
    ADD CONSTRAINT uq_app_config_definitions_config_name UNIQUE (config_name);


--
-- Name: app_config_fragments uq_app_config_fragments_config_name_scope_type_scope_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_fragments
    ADD CONSTRAINT uq_app_config_fragments_config_name_scope_type_scope_id UNIQUE NULLS NOT DISTINCT (config_name, scope_type, scope_id);


--
-- Name: artifact_revisions uq_artifact_id_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_revisions
    ADD CONSTRAINT uq_artifact_id_version UNIQUE (artifact_id, version);


--
-- Name: artifact_registries uq_artifact_registries_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_registries
    ADD CONSTRAINT uq_artifact_registries_name UNIQUE (name);


--
-- Name: artifact_registries uq_artifact_registries_registry_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifact_registries
    ADD CONSTRAINT uq_artifact_registries_registry_id UNIQUE (registry_id);


--
-- Name: association_artifacts_storages uq_artifact_revision_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_artifacts_storages
    ADD CONSTRAINT uq_artifact_revision_id UNIQUE (artifact_revision_id);


--
-- Name: association_groups_users uq_association_user_id_group_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_groups_users
    ADD CONSTRAINT uq_association_user_id_group_id UNIQUE (user_id, group_id);


--
-- Name: audit_log_scopes uq_audit_log_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log_scopes
    ADD CONSTRAINT uq_audit_log_scope UNIQUE (audit_log_id, scope_type, scope_id);


--
-- Name: auto_generated_file_revisions uq_auto_generated_file_revisions_file_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_file_revisions
    ADD CONSTRAINT uq_auto_generated_file_revisions_file_id UNIQUE (file_id, revision_number);


--
-- Name: bootstrap_script_revisions uq_bootstrap_script_revisions_script_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bootstrap_script_revisions
    ADD CONSTRAINT uq_bootstrap_script_revisions_script_id UNIQUE (script_id, revision_number);


--
-- Name: client_ip_masking_policies uq_client_ip_masking_policies_target_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_ip_masking_policies
    ADD CONSTRAINT uq_client_ip_masking_policies_target_type UNIQUE (target_type);


--
-- Name: deployment_auto_scaling_policies uq_deployment_auto_scaling_policies_endpoint; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_auto_scaling_policies
    ADD CONSTRAINT uq_deployment_auto_scaling_policies_endpoint UNIQUE (endpoint);


--
-- Name: deployment_policies uq_deployment_policies_endpoint; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_policies
    ADD CONSTRAINT uq_deployment_policies_endpoint UNIQUE (endpoint);


--
-- Name: deployment_revision_presets uq_deployment_revision_presets_variant_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_presets
    ADD CONSTRAINT uq_deployment_revision_presets_variant_name UNIQUE (runtime_variant, name);


--
-- Name: deployment_revision_resource_slots uq_deployment_revision_resource_slots_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_resource_slots
    ADD CONSTRAINT uq_deployment_revision_resource_slots_id UNIQUE (id);


--
-- Name: deployment_revisions uq_deployment_revisions_endpoint_revision_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT uq_deployment_revisions_endpoint_revision_number UNIQUE (endpoint, revision_number);


--
-- Name: domain_fair_shares uq_domain_fair_share_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_fair_shares
    ADD CONSTRAINT uq_domain_fair_share_rg_id UNIQUE (resource_group_id, domain_name);


--
-- Name: domain_usage_buckets uq_domain_usage_bucket_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_usage_buckets
    ADD CONSTRAINT uq_domain_usage_bucket_rg_id UNIQUE (domain_name, resource_group_id, period_start);


--
-- Name: domains uq_domains_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domains
    ADD CONSTRAINT uq_domains_id UNIQUE (id);


--
-- Name: entity_fields uq_entity_fields_mapping; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_fields
    ADD CONSTRAINT uq_entity_fields_mapping UNIQUE (entity_type, entity_id, field_type, field_id);


--
-- Name: entity_labels uq_entity_labels_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_labels
    ADD CONSTRAINT uq_entity_labels_key UNIQUE (entity_type, entity_id, key);


--
-- Name: entity_membership_caps uq_entity_membership_caps_bit; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_membership_caps
    ADD CONSTRAINT uq_entity_membership_caps_bit UNIQUE (membership_id, permission);


--
-- Name: entity_memberships uq_entity_memberships_edge; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_memberships
    ADD CONSTRAINT uq_entity_memberships_edge UNIQUE (virtual_entity_id, member_entity_id);


--
-- Name: global_entities uq_global_entities_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.global_entities
    ADD CONSTRAINT uq_global_entities_name UNIQUE (name);


--
-- Name: groups uq_groups_name_domain_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT uq_groups_name_domain_name UNIQUE (name, domain_name);


--
-- Name: idle_checker_bindings uq_idle_checker_bindings_checker_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idle_checker_bindings
    ADD CONSTRAINT uq_idle_checker_bindings_checker_scope UNIQUE (idle_checker_id, scope_type, scope_id);


--
-- Name: images uq_image_identifier; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.images
    ADD CONSTRAINT uq_image_identifier UNIQUE (registry, project, name, tag, architecture);


--
-- Name: kernel_group_environ uq_kernel_group_environ_kernel_group_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_environ
    ADD CONSTRAINT uq_kernel_group_environ_kernel_group_id UNIQUE (kernel_group_id, key);


--
-- Name: kernel_group_resource_slots uq_kernel_group_resource_slots_kernel_group_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_resource_slots
    ADD CONSTRAINT uq_kernel_group_resource_slots_kernel_group_id UNIQUE (kernel_group_id, slot_name);


--
-- Name: kernel_group_vfolder_mounts uq_kernel_group_vfolder_mounts_kernel_group_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_vfolder_mounts
    ADD CONSTRAINT uq_kernel_group_vfolder_mounts_kernel_group_id UNIQUE (kernel_group_id, mount_destination);


--
-- Name: kernel_groups uq_kernel_groups_session_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_groups
    ADD CONSTRAINT uq_kernel_groups_session_id UNIQUE (session_id, role);


--
-- Name: keypair_resource_policies uq_keypair_resource_policies_uuid; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypair_resource_policies
    ADD CONSTRAINT uq_keypair_resource_policies_uuid UNIQUE (uuid);


--
-- Name: keypairs uq_keypairs_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypairs
    ADD CONSTRAINT uq_keypairs_id UNIQUE (id);


--
-- Name: login_client_types uq_login_client_types_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_client_types
    ADD CONSTRAINT uq_login_client_types_name UNIQUE (name);


--
-- Name: model_card_resource_requirements uq_model_card_resource_requirements_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_card_resource_requirements
    ADD CONSTRAINT uq_model_card_resource_requirements_id UNIQUE (id);


--
-- Name: model_cards uq_model_cards_name_domain_project; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT uq_model_cards_name_domain_project UNIQUE (name, domain, project);


--
-- Name: organization_auto_generated_file_relations uq_organization_auto_generated_file_relations_path; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_auto_generated_file_relations
    ADD CONSTRAINT uq_organization_auto_generated_file_relations_path UNIQUE (organization_type, organization_id, path);


--
-- Name: permissions uq_permissions_role_entity_permission; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uq_permissions_role_entity_permission UNIQUE (role_id, entity_type, permission);


--
-- Name: preset_resource_slots uq_preset_resource_slots_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preset_resource_slots
    ADD CONSTRAINT uq_preset_resource_slots_id UNIQUE (id);


--
-- Name: project_fair_shares uq_project_fair_share_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_fair_shares
    ADD CONSTRAINT uq_project_fair_share_rg_id UNIQUE (resource_group_id, project_id);


--
-- Name: project_resource_policies uq_project_resource_policies_uuid; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_resource_policies
    ADD CONSTRAINT uq_project_resource_policies_uuid UNIQUE (uuid);


--
-- Name: project_usage_buckets uq_project_usage_bucket_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_usage_buckets
    ADD CONSTRAINT uq_project_usage_bucket_rg_id UNIQUE (project_id, resource_group_id, period_start);


--
-- Name: prometheus_query_preset_categories uq_prometheus_query_preset_categories_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prometheus_query_preset_categories
    ADD CONSTRAINT uq_prometheus_query_preset_categories_name UNIQUE (name);


--
-- Name: association_container_registries_groups uq_registry_id_project_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_container_registries_groups
    ADD CONSTRAINT uq_registry_id_project_id UNIQUE (registry_id, project_id);


--
-- Name: resource_allocations uq_resource_allocations_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT uq_resource_allocations_id UNIQUE (id);


--
-- Name: resource_slot_types uq_resource_slot_types_uuid; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_slot_types
    ADD CONSTRAINT uq_resource_slot_types_uuid UNIQUE (uuid);


--
-- Name: retention_policies uq_retention_policies_category; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.retention_policies
    ADD CONSTRAINT uq_retention_policies_category UNIQUE (category);


--
-- Name: role_permission_presets uq_role_permission_presets_preset_entity_op; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission_presets
    ADD CONSTRAINT uq_role_permission_presets_preset_entity_op UNIQUE (role_preset_id, entity_type, permission);


--
-- Name: role_presets uq_role_presets_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_presets
    ADD CONSTRAINT uq_role_presets_name UNIQUE NULLS NOT DISTINCT (name, scope_type, scope_id);


--
-- Name: routings uq_routings_endpoint_session; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT uq_routings_endpoint_session UNIQUE (endpoint, session);


--
-- Name: runtime_variant_presets uq_runtime_variant_presets_variant_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_variant_presets
    ADD CONSTRAINT uq_runtime_variant_presets_variant_name UNIQUE (runtime_variant, name);


--
-- Name: runtime_variants uq_runtime_variants_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runtime_variants
    ADD CONSTRAINT uq_runtime_variants_name UNIQUE (name);


--
-- Name: scaling_groups uq_scaling_groups_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scaling_groups
    ADD CONSTRAINT uq_scaling_groups_id UNIQUE (id);


--
-- Name: service_catalog_endpoint uq_service_catalog_endpoint_service_id_role_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_catalog_endpoint
    ADD CONSTRAINT uq_service_catalog_endpoint_service_id_role_scope UNIQUE (service_id, role, scope);


--
-- Name: service_catalog uq_service_catalog_service_group_instance_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_catalog
    ADD CONSTRAINT uq_service_catalog_service_group_instance_id UNIQUE (service_group, instance_id);


--
-- Name: session_dependencies uq_session_dependencies_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_dependencies
    ADD CONSTRAINT uq_session_dependencies_id UNIQUE (id);


--
-- Name: session_designated_agents uq_session_designated_agents_session_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_designated_agents
    ADD CONSTRAINT uq_session_designated_agents_session_id UNIQUE (session_id, agent_uuid);


--
-- Name: sgroups_for_keypairs uq_sgroup_akey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_keypairs
    ADD CONSTRAINT uq_sgroup_akey UNIQUE (resource_group_id, access_key);


--
-- Name: sgroups_for_domains uq_sgroup_domain; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_domains
    ADD CONSTRAINT uq_sgroup_domain UNIQUE (resource_group_id, domain_id);


--
-- Name: sgroups_for_groups uq_sgroup_ugroup; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_groups
    ADD CONSTRAINT uq_sgroup_ugroup UNIQUE (resource_group_id, "group");


--
-- Name: storage_backend_types uq_storage_backend_types_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_backend_types
    ADD CONSTRAINT uq_storage_backend_types_name UNIQUE (name);


--
-- Name: storage_backends uq_storage_backends_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_backends
    ADD CONSTRAINT uq_storage_backends_name UNIQUE (name);


--
-- Name: storage_namespace uq_storage_id_namespace; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_namespace
    ADD CONSTRAINT uq_storage_id_namespace UNIQUE (storage_id, namespace);


--
-- Name: storage_volumes uq_storage_volumes_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volumes
    ADD CONSTRAINT uq_storage_volumes_name UNIQUE (name);


--
-- Name: system_session_environ uq_system_session_environ_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_session_environ
    ADD CONSTRAINT uq_system_session_environ_key UNIQUE (key, scope_type, scope_id);


--
-- Name: user_fair_shares uq_user_fair_share_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_fair_shares
    ADD CONSTRAINT uq_user_fair_share_rg_id UNIQUE (resource_group_id, user_uuid, project_id);


--
-- Name: user_roles uq_user_id_role_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT uq_user_id_role_id UNIQUE (user_id, role_id);


--
-- Name: user_resource_policies uq_user_resource_policies_uuid; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_resource_policies
    ADD CONSTRAINT uq_user_resource_policies_uuid UNIQUE (uuid);


--
-- Name: user_usage_buckets uq_user_usage_bucket_rg_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_usage_buckets
    ADD CONSTRAINT uq_user_usage_bucket_rg_id UNIQUE (user_uuid, project_id, resource_group_id, period_start);


--
-- Name: users uq_users_username; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_username UNIQUE (username);


--
-- Name: vfolder_user_mount_policies uq_vfolder_user_mount_policies_vfolder_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_user_mount_policies
    ADD CONSTRAINT uq_vfolder_user_mount_policies_vfolder_id UNIQUE (vfolder_id, user_id);


--
-- Name: virtual_entities uq_virtual_entities_entity; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.virtual_entities
    ADD CONSTRAINT uq_virtual_entities_entity UNIQUE (entity_type, entity_id);


--
-- Name: ix_agent_installed_images_image_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agent_installed_images_image_id ON public.agent_installed_images USING btree (image_id);


--
-- Name: ix_agent_resources_agent_avail; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agent_resources_agent_avail ON public.agent_resources USING btree (agent_id, slot_name, capacity, reserved, used);


--
-- Name: ix_agent_resources_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agent_resources_slot_name ON public.agent_resources USING btree (slot_name);


--
-- Name: ix_agents_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agents_region ON public.agents USING btree (region);


--
-- Name: ix_agents_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agents_resource_group_id ON public.agents USING btree (resource_group_id);


--
-- Name: ix_agents_scaling_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agents_scaling_group ON public.agents USING btree (scaling_group);


--
-- Name: ix_agents_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agents_status ON public.agents USING btree (status);


--
-- Name: ix_artifact_revisions_artifact_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifact_revisions_artifact_id ON public.artifact_revisions USING btree (artifact_id);


--
-- Name: ix_artifact_revisions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifact_revisions_created_at ON public.artifact_revisions USING btree (created_at);


--
-- Name: ix_artifact_revisions_remote_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifact_revisions_remote_status ON public.artifact_revisions USING btree (remote_status);


--
-- Name: ix_artifact_revisions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifact_revisions_status ON public.artifact_revisions USING btree (status);


--
-- Name: ix_artifact_revisions_updated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifact_revisions_updated_at ON public.artifact_revisions USING btree (updated_at);


--
-- Name: ix_artifacts_availability; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_availability ON public.artifacts USING btree (availability);


--
-- Name: ix_artifacts_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_name ON public.artifacts USING btree (name);


--
-- Name: ix_artifacts_registry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_registry_id ON public.artifacts USING btree (registry_id);


--
-- Name: ix_artifacts_registry_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_registry_type ON public.artifacts USING btree (registry_type);


--
-- Name: ix_artifacts_source_registry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_source_registry_id ON public.artifacts USING btree (source_registry_id);


--
-- Name: ix_artifacts_source_registry_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_source_registry_type ON public.artifacts USING btree (source_registry_type);


--
-- Name: ix_artifacts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_artifacts_type ON public.artifacts USING btree (type);


--
-- Name: ix_audit_log_scopes_audit_log_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_scopes_audit_log_id ON public.audit_log_scopes USING btree (audit_log_id);


--
-- Name: ix_audit_log_scopes_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_log_scopes_scope ON public.audit_log_scopes USING btree (scope_type, scope_id);


--
-- Name: ix_audit_logs_action_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_action_name ON public.audit_logs USING btree (action_name);


--
-- Name: ix_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: ix_audit_logs_entity_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_id ON public.audit_logs USING btree (entity_id);


--
-- Name: ix_audit_logs_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_entity_type ON public.audit_logs USING btree (entity_type);


--
-- Name: ix_audit_logs_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_lookup ON public.audit_logs USING btree (lookup_kind, lookup_key);


--
-- Name: ix_audit_logs_operation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_logs_operation ON public.audit_logs USING btree (operation);


--
-- Name: ix_container_registries_is_global; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_is_global ON public.container_registries USING btree (is_global);


--
-- Name: ix_container_registries_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_project ON public.container_registries USING btree (project);


--
-- Name: ix_container_registries_registry_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_registry_name ON public.container_registries USING btree (registry_name);


--
-- Name: ix_container_registries_ssl_verify; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_ssl_verify ON public.container_registries USING btree (ssl_verify);


--
-- Name: ix_container_registries_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_type ON public.container_registries USING btree (type);


--
-- Name: ix_container_registries_url; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_container_registries_url ON public.container_registries USING btree (url);


--
-- Name: ix_deployment_auto_scaling_policies_endpoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_auto_scaling_policies_endpoint ON public.deployment_auto_scaling_policies USING btree (endpoint);


--
-- Name: ix_deployment_designated_agents_agent_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_designated_agents_agent_uuid ON public.deployment_designated_agents USING btree (agent_uuid);


--
-- Name: ix_deployment_history_deployment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_history_deployment_id ON public.deployment_history USING btree (deployment_id);


--
-- Name: ix_deployment_policies_endpoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_policies_endpoint ON public.deployment_policies USING btree (endpoint);


--
-- Name: ix_deployment_revision_presets_variant_rank; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_revision_presets_variant_rank ON public.deployment_revision_presets USING btree (runtime_variant, rank);


--
-- Name: ix_deployment_revisions_endpoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_deployment_revisions_endpoint ON public.deployment_revisions USING btree (endpoint);


--
-- Name: ix_domain_container_registry_relations_container_registry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_container_registry_relations_container_registry_id ON public.domain_container_registry_relations USING btree (container_registry_id);


--
-- Name: ix_domain_fair_share_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_fair_share_lookup ON public.domain_fair_shares USING btree (resource_group, domain_name);


--
-- Name: ix_domain_fair_shares_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_fair_shares_domain_name ON public.domain_fair_shares USING btree (domain_name);


--
-- Name: ix_domain_fair_shares_resource_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_fair_shares_resource_group ON public.domain_fair_shares USING btree (resource_group);


--
-- Name: ix_domain_usage_bucket_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_usage_bucket_lookup ON public.domain_usage_buckets USING btree (domain_name, resource_group, period_start);


--
-- Name: ix_domain_usage_buckets_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domain_usage_buckets_domain_name ON public.domain_usage_buckets USING btree (domain_name);


--
-- Name: ix_domains_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_domains_status ON public.domains USING btree (status);


--
-- Name: ix_dr_resource_slots_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dr_resource_slots_slot_name ON public.deployment_revision_resource_slots USING btree (slot_name);


--
-- Name: ix_endpoints_lifecycle_sub_step; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_endpoints_lifecycle_sub_step ON public.endpoints USING btree (lifecycle_stage, sub_step);


--
-- Name: ix_endpoints_resource_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_endpoints_resource_group ON public.endpoints USING btree (resource_group);


--
-- Name: ix_entity_fields_entity_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_fields_entity_lookup ON public.entity_fields USING btree (entity_type, entity_id);


--
-- Name: ix_entity_fields_field_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_fields_field_lookup ON public.entity_fields USING btree (field_type, field_id);


--
-- Name: ix_entity_labels_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_labels_entity ON public.entity_labels USING btree (entity_type, entity_id);


--
-- Name: ix_entity_labels_pair; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_labels_pair ON public.entity_labels USING btree (key, value);


--
-- Name: ix_entity_memberships_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_memberships_entity ON public.entity_memberships USING btree (member_entity_id) INCLUDE (virtual_entity_id, capped);


--
-- Name: ix_entity_shares_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_shares_recipient ON public.entity_shares USING btree (recipient_entity_type, recipient_entity_id);


--
-- Name: ix_entity_shares_recipient_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_shares_recipient_email ON public.entity_shares USING btree (recipient_email);


--
-- Name: ix_entity_shares_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_entity_shares_target ON public.entity_shares USING btree (target_entity_type, target_entity_id);


--
-- Name: ix_error_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_logs_created_at ON public.error_logs USING btree (created_at);


--
-- Name: ix_error_logs_is_cleared; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_logs_is_cleared ON public.error_logs USING btree (is_cleared);


--
-- Name: ix_error_logs_is_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_logs_is_read ON public.error_logs USING btree (is_read);


--
-- Name: ix_error_logs_severity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_logs_severity ON public.error_logs USING btree (severity);


--
-- Name: ix_error_logs_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_error_logs_user ON public.error_logs USING btree ("user");


--
-- Name: ix_event_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_logs_created_at ON public.event_logs USING btree (created_at);


--
-- Name: ix_event_logs_domain_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_event_logs_domain_id ON public.event_logs USING btree (domain_id);


--
-- Name: ix_groups_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_groups_domain_name ON public.groups USING btree (domain_name);


--
-- Name: ix_groups_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_groups_status ON public.groups USING btree (status);


--
-- Name: ix_id_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_id_status ON public.roles USING btree (id, status);


--
-- Name: ix_idle_checker_bindings_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_idle_checker_bindings_scope ON public.idle_checker_bindings USING btree (scope_type, scope_id);


--
-- Name: ix_image_aliases_alias; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_image_aliases_alias ON public.image_aliases USING btree (alias);


--
-- Name: ix_images_architecture; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_architecture ON public.images USING btree (architecture);


--
-- Name: ix_images_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_created_at ON public.images USING btree (created_at);


--
-- Name: ix_images_creator_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_creator_id ON public.images USING btree (creator_id);


--
-- Name: ix_images_image; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_image ON public.images USING btree (image);


--
-- Name: ix_images_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_name ON public.images USING btree (name);


--
-- Name: ix_images_registry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_registry ON public.images USING btree (registry);


--
-- Name: ix_images_registry_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_images_registry_id ON public.images USING btree (registry_id);


--
-- Name: ix_kernel_group_resource_slots_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_group_resource_slots_slot_name ON public.kernel_group_resource_slots USING btree (slot_name);


--
-- Name: ix_kernel_group_vfolder_mounts_vfolder_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_group_vfolder_mounts_vfolder_id ON public.kernel_group_vfolder_mounts USING btree (vfolder_id);


--
-- Name: ix_kernel_groups_image_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_groups_image_id ON public.kernel_groups USING btree (image_id);


--
-- Name: ix_kernel_scheduling_history_kernel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_scheduling_history_kernel_id ON public.kernel_scheduling_history USING btree (kernel_id);


--
-- Name: ix_kernel_scheduling_history_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_scheduling_history_session_id ON public.kernel_scheduling_history USING btree (session_id);


--
-- Name: ix_kernel_usage_records_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_records_domain_name ON public.kernel_usage_records USING btree (domain_name);


--
-- Name: ix_kernel_usage_records_kernel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_records_kernel_id ON public.kernel_usage_records USING btree (kernel_id);


--
-- Name: ix_kernel_usage_records_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_records_project_id ON public.kernel_usage_records USING btree (project_id);


--
-- Name: ix_kernel_usage_records_resource_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_records_resource_group ON public.kernel_usage_records USING btree (resource_group);


--
-- Name: ix_kernel_usage_records_user_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_records_user_uuid ON public.kernel_usage_records USING btree (user_uuid);


--
-- Name: ix_kernel_usage_rg_id_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_rg_id_period ON public.kernel_usage_records USING btree (resource_group_id, period_start);


--
-- Name: ix_kernel_usage_rg_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_rg_period ON public.kernel_usage_records USING btree (resource_group, period_start);


--
-- Name: ix_kernel_usage_user_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernel_usage_user_period ON public.kernel_usage_records USING btree (user_uuid, period_start);


--
-- Name: ix_kernels_cluster_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_cluster_role ON public.kernels USING btree (cluster_role);


--
-- Name: ix_kernels_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_created_at ON public.kernels USING btree (created_at);


--
-- Name: ix_kernels_fair_share_running; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_fair_share_running ON public.kernels USING btree (scaling_group) WHERE ((terminated_at IS NULL) AND (starts_at IS NOT NULL));


--
-- Name: ix_kernels_fair_share_terminated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_fair_share_terminated ON public.kernels USING btree (scaling_group, terminated_at) WHERE ((terminated_at IS NOT NULL) AND (starts_at IS NOT NULL));


--
-- Name: ix_kernels_image_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_image_id ON public.kernels USING btree (image_id);


--
-- Name: ix_kernels_kernel_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_kernel_group_id ON public.kernels USING btree (kernel_group_id);


--
-- Name: ix_kernels_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_resource_group_id ON public.kernels USING btree (resource_group_id);


--
-- Name: ix_kernels_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_result ON public.kernels USING btree (result);


--
-- Name: ix_kernels_scaling_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_scaling_group ON public.kernels USING btree (scaling_group);


--
-- Name: ix_kernels_sess_id_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_sess_id_role ON public.kernels USING btree (session_id, cluster_role);


--
-- Name: ix_kernels_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_session_id ON public.kernels USING btree (session_id);


--
-- Name: ix_kernels_session_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_session_name ON public.kernels USING btree (session_name);


--
-- Name: ix_kernels_session_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_session_type ON public.kernels USING btree (session_type);


--
-- Name: ix_kernels_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_status ON public.kernels USING btree (status);


--
-- Name: ix_kernels_status_changed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_status_changed ON public.kernels USING btree (status_changed);


--
-- Name: ix_kernels_status_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_status_role ON public.kernels USING btree (status, cluster_role);


--
-- Name: ix_kernels_terminated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_terminated_at ON public.kernels USING btree (terminated_at);


--
-- Name: ix_kernels_updated_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kernels_updated_order ON public.kernels USING btree (GREATEST('created_at'::text, 'terminated_at'::text, 'status_changed'::text));


--
-- Name: ix_keypairs_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_keypairs_is_active ON public.keypairs USING btree (is_active);


--
-- Name: ix_keypairs_is_admin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_keypairs_is_admin ON public.keypairs USING btree (is_admin);


--
-- Name: ix_login_history_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_created_at ON public.login_history USING btree (created_at);


--
-- Name: ix_login_history_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_result ON public.login_history USING btree (result);


--
-- Name: ix_login_history_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_user_id ON public.login_history USING btree (user_id);


--
-- Name: ix_login_history_user_id_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_history_user_id_created_at ON public.login_history USING btree (user_id, created_at);


--
-- Name: ix_login_sessions_login_client_type_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_sessions_login_client_type_id ON public.login_sessions USING btree (login_client_type_id);


--
-- Name: ix_login_sessions_session_token; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_login_sessions_session_token ON public.login_sessions USING btree (session_token);


--
-- Name: ix_login_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_sessions_status ON public.login_sessions USING btree (status);


--
-- Name: ix_login_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_sessions_user_id ON public.login_sessions USING btree (user_id);


--
-- Name: ix_login_sessions_user_id_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_sessions_user_id_status ON public.login_sessions USING btree (user_id, status);


--
-- Name: ix_mc_resource_req_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_mc_resource_req_slot_name ON public.model_card_resource_requirements USING btree (slot_name);


--
-- Name: ix_notification_channels_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_channels_enabled ON public.notification_channels USING btree (enabled);


--
-- Name: ix_notification_rules_enabled; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_rules_enabled ON public.notification_rules USING btree (enabled);


--
-- Name: ix_notification_rules_rule_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notification_rules_rule_type ON public.notification_rules USING btree (rule_type);


--
-- Name: ix_object_storages_host; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_object_storages_host ON public.object_storages USING btree (host);


--
-- Name: ix_object_storages_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_object_storages_name ON public.object_storages USING btree (name);


--
-- Name: ix_organization_auto_generated_file_relations_file_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_organization_auto_generated_file_relations_file_id ON public.organization_auto_generated_file_relations USING btree (file_id);


--
-- Name: ix_permissions_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_permissions_entity ON public.permissions USING btree (entity_type) INCLUDE (permission, role_id);


--
-- Name: ix_preset_resource_slots_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_preset_resource_slots_slot_name ON public.preset_resource_slots USING btree (slot_name);


--
-- Name: ix_project_fair_share_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_fair_share_lookup ON public.project_fair_shares USING btree (resource_group, project_id);


--
-- Name: ix_project_fair_shares_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_fair_shares_domain_name ON public.project_fair_shares USING btree (domain_name);


--
-- Name: ix_project_fair_shares_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_fair_shares_project_id ON public.project_fair_shares USING btree (project_id);


--
-- Name: ix_project_fair_shares_resource_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_fair_shares_resource_group ON public.project_fair_shares USING btree (resource_group);


--
-- Name: ix_project_usage_bucket_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_usage_bucket_lookup ON public.project_usage_buckets USING btree (project_id, resource_group, period_start);


--
-- Name: ix_project_usage_buckets_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_usage_buckets_domain_name ON public.project_usage_buckets USING btree (domain_name);


--
-- Name: ix_project_usage_buckets_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_project_usage_buckets_project_id ON public.project_usage_buckets USING btree (project_id);


--
-- Name: ix_ra_kernel_slot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ra_kernel_slot ON public.resource_allocations USING btree (kernel_id, slot_name);


--
-- Name: ix_ra_occupied; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ra_occupied ON public.resource_allocations USING btree (kernel_id, slot_name) WHERE (free_at IS NULL);


--
-- Name: ix_replica_group_history_deployment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replica_group_history_deployment_id ON public.replica_group_history USING btree (deployment_id);


--
-- Name: ix_replica_group_history_replica_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replica_group_history_replica_group_id ON public.replica_group_history USING btree (replica_group_id);


--
-- Name: ix_replica_groups_deployment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_replica_groups_deployment_id ON public.replica_groups USING btree (deployment_id);


--
-- Name: ix_resource_allocations_slot_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_resource_allocations_slot_name ON public.resource_allocations USING btree (slot_name);


--
-- Name: ix_resource_presets_name_null_scaling_group_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_resource_presets_name_null_scaling_group_name ON public.resource_presets USING btree (name) WHERE (scaling_group_name IS NULL);


--
-- Name: ix_resource_presets_name_scaling_group_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_resource_presets_name_scaling_group_name ON public.resource_presets USING btree (name, scaling_group_name) WHERE (scaling_group_name IS NOT NULL);


--
-- Name: ix_role_presets_scope_type_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_role_presets_scope_type_deleted_at ON public.role_presets USING btree (scope_type, deleted_at);


--
-- Name: ix_roles_role_preset_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_role_preset_id ON public.roles USING btree (role_preset_id);


--
-- Name: ix_roles_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_roles_scope ON public.roles USING btree (scope_type, scope_id);


--
-- Name: ix_route_history_deployment_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_history_deployment_id ON public.route_history USING btree (deployment_id);


--
-- Name: ix_route_history_route_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_route_history_route_id ON public.route_history USING btree (route_id);


--
-- Name: ix_routings_replica_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_routings_replica_group_id ON public.routings USING btree (replica_group_id);


--
-- Name: ix_runtime_variant_presets_variant_rank; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_runtime_variant_presets_variant_rank ON public.runtime_variant_presets USING btree (runtime_variant, rank);


--
-- Name: ix_scaling_groups_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scaling_groups_is_active ON public.scaling_groups USING btree (is_active);


--
-- Name: ix_scaling_groups_is_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scaling_groups_is_public ON public.scaling_groups USING btree (is_public);


--
-- Name: ix_scope_bindings_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scope_bindings_scope ON public.scope_bindings USING btree (scope_entity_id);


--
-- Name: ix_scope_bindings_virtual_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scope_bindings_virtual_entity ON public.scope_bindings USING btree (virtual_entity_id) INCLUDE (scope_entity_id, permission_cap);


--
-- Name: ix_service_catalog_service_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_catalog_service_group ON public.service_catalog USING btree (service_group);


--
-- Name: ix_service_catalog_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_service_catalog_status ON public.service_catalog USING btree (status);


--
-- Name: ix_session_dependencies_depends_on; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_dependencies_depends_on ON public.session_dependencies USING btree (depends_on);


--
-- Name: ix_session_dependencies_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_dependencies_session_id ON public.session_dependencies USING btree (session_id);


--
-- Name: ix_session_designated_agents_agent_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_designated_agents_agent_uuid ON public.session_designated_agents USING btree (agent_uuid);


--
-- Name: ix_session_idle_checks_expire_at_not_null; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_idle_checks_expire_at_not_null ON public.session_idle_checks USING btree (expire_at) WHERE (expire_at IS NOT NULL);


--
-- Name: ix_session_scheduling_history_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_scheduling_history_session_id ON public.session_scheduling_history USING btree (session_id);


--
-- Name: ix_session_status_with_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_status_with_priority ON public.sessions USING btree (status, priority);


--
-- Name: ix_session_templates_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_templates_created_at ON public.session_templates USING btree (created_at);


--
-- Name: ix_session_templates_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_templates_type ON public.session_templates USING btree (type);


--
-- Name: ix_session_templates_user_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_session_templates_user_uuid ON public.session_templates USING btree (user_uuid);


--
-- Name: ix_sessions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_created_at ON public.sessions USING btree (created_at);


--
-- Name: ix_sessions_domain_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_domain_id ON public.sessions USING btree (domain_id);


--
-- Name: ix_sessions_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_name ON public.sessions USING btree (name);


--
-- Name: ix_sessions_priority; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_priority ON public.sessions USING btree (priority);


--
-- Name: ix_sessions_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_resource_group_id ON public.sessions USING btree (resource_group_id);


--
-- Name: ix_sessions_result; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_result ON public.sessions USING btree (result);


--
-- Name: ix_sessions_scaling_group_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_scaling_group_name ON public.sessions USING btree (scaling_group_name);


--
-- Name: ix_sessions_session_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_session_group_id ON public.sessions USING btree (session_group_id);


--
-- Name: ix_sessions_session_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_session_type ON public.sessions USING btree (session_type);


--
-- Name: ix_sessions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_status ON public.sessions USING btree (status);


--
-- Name: ix_sessions_terminated_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_terminated_at ON public.sessions USING btree (terminated_at);


--
-- Name: ix_sessions_unique_name_per_user_nonterminal; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_sessions_unique_name_per_user_nonterminal ON public.sessions USING btree (name, user_uuid) WHERE ((status)::text <> ALL ((ARRAY['ERROR'::character varying, 'TERMINATED'::character varying, 'CANCELLED'::character varying])::text[]));


--
-- Name: ix_sessions_updated_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_updated_order ON public.sessions USING btree (GREATEST('created_at'::text, 'terminated_at'::text));


--
-- Name: ix_sessions_vfolder_mounts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_vfolder_mounts ON public.sessions USING gin (vfolder_mounts);


--
-- Name: ix_sgroups_for_domains_domain_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_domains_domain_id ON public.sgroups_for_domains USING btree (domain_id);


--
-- Name: ix_sgroups_for_domains_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_domains_resource_group_id ON public.sgroups_for_domains USING btree (resource_group_id);


--
-- Name: ix_sgroups_for_groups_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_groups_group ON public.sgroups_for_groups USING btree ("group");


--
-- Name: ix_sgroups_for_groups_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_groups_resource_group_id ON public.sgroups_for_groups USING btree (resource_group_id);


--
-- Name: ix_sgroups_for_keypairs_access_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_keypairs_access_key ON public.sgroups_for_keypairs USING btree (access_key);


--
-- Name: ix_sgroups_for_keypairs_resource_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sgroups_for_keypairs_resource_group_id ON public.sgroups_for_keypairs USING btree (resource_group_id);


--
-- Name: ix_ssh_keypairs_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_ssh_keypairs_user_id ON public.ssh_keypairs USING btree (user_id);


--
-- Name: ix_system_session_environ_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_system_session_environ_scope ON public.system_session_environ USING btree (scope_type, scope_id);


--
-- Name: ix_usage_bucket_entries_bucket_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_usage_bucket_entries_bucket_type ON public.usage_bucket_entries USING btree (bucket_type);


--
-- Name: ix_usage_bucket_entries_slot; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_usage_bucket_entries_slot ON public.usage_bucket_entries USING btree (slot_name);


--
-- Name: ix_user_default_bootstrap_scripts_script_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_default_bootstrap_scripts_script_id ON public.user_default_bootstrap_scripts USING btree (script_id);


--
-- Name: ix_user_fair_share_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_fair_share_lookup ON public.user_fair_shares USING btree (resource_group, user_uuid, project_id);


--
-- Name: ix_user_fair_shares_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_fair_shares_domain_name ON public.user_fair_shares USING btree (domain_name);


--
-- Name: ix_user_fair_shares_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_fair_shares_project_id ON public.user_fair_shares USING btree (project_id);


--
-- Name: ix_user_fair_shares_resource_group; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_fair_shares_resource_group ON public.user_fair_shares USING btree (resource_group);


--
-- Name: ix_user_fair_shares_user_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_fair_shares_user_uuid ON public.user_fair_shares USING btree (user_uuid);


--
-- Name: ix_user_usage_bucket_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_usage_bucket_lookup ON public.user_usage_buckets USING btree (user_uuid, project_id, resource_group, period_start);


--
-- Name: ix_user_usage_buckets_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_usage_buckets_domain_name ON public.user_usage_buckets USING btree (domain_name);


--
-- Name: ix_user_usage_buckets_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_usage_buckets_project_id ON public.user_usage_buckets USING btree (project_id);


--
-- Name: ix_user_usage_buckets_user_uuid; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_usage_buckets_user_uuid ON public.user_usage_buckets USING btree (user_uuid);


--
-- Name: ix_users_domain_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_domain_id ON public.users USING btree (domain_id);


--
-- Name: ix_users_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_domain_name ON public.users USING btree (domain_name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_vfolders_domain_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_domain_name ON public.vfolders USING btree (domain_name);


--
-- Name: ix_vfolders_host; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_host ON public.vfolders USING btree (host);


--
-- Name: ix_vfolders_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_name ON public.vfolders USING btree (name);


--
-- Name: ix_vfolders_ownership_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_ownership_type ON public.vfolders USING btree (ownership_type);


--
-- Name: ix_vfolders_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_status ON public.vfolders USING btree (status);


--
-- Name: ix_vfolders_status_changed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_status_changed ON public.vfolders USING btree (status_changed);


--
-- Name: ix_vfolders_usage_mode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_vfolders_usage_mode ON public.vfolders USING btree (usage_mode);


--
-- Name: ix_vfs_storages_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_vfs_storages_name ON public.vfs_storages USING btree (name);


--
-- Name: uq_auto_generated_files_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_auto_generated_files_is_default ON public.auto_generated_files USING btree (entity_type, entity_id, path) WHERE is_default;


--
-- Name: uq_domains_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_domains_is_default ON public.domains USING btree (is_default) WHERE is_default;


--
-- Name: uq_entity_shares_live_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_entity_shares_live_email ON public.entity_shares USING btree (recipient_email, target_entity_type, target_entity_id) WHERE (((status)::text = ANY ((ARRAY['pending'::character varying, 'accepted'::character varying])::text[])) AND (recipient_email IS NOT NULL));


--
-- Name: uq_entity_shares_live_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_entity_shares_live_recipient ON public.entity_shares USING btree (recipient_entity_type, recipient_entity_id, target_entity_type, target_entity_id) WHERE (((status)::text = ANY ((ARRAY['pending'::character varying, 'accepted'::character varying])::text[])) AND (recipient_entity_type IS NOT NULL));


--
-- Name: uq_groups_personal_creator; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_groups_personal_creator ON public.groups USING btree (creator_id) WHERE ((type)::text = 'personal'::text);


--
-- Name: uq_keypair_resource_policies_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_keypair_resource_policies_is_default ON public.keypair_resource_policies USING btree (is_default) WHERE is_default;


--
-- Name: uq_keypairs_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_keypairs_is_default ON public.keypairs USING btree ("user") WHERE is_default;


--
-- Name: uq_project_default_registry; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_project_default_registry ON public.association_container_registries_groups USING btree (project_id) WHERE is_default;


--
-- Name: uq_resource_group_volume_offers_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_resource_group_volume_offers_is_default ON public.resource_group_volume_offers USING btree (resource_group_id) WHERE is_default;


--
-- Name: uq_roles_preset_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_roles_preset_scope ON public.roles USING btree (role_preset_id, scope_type, scope_id) WHERE (role_preset_id IS NOT NULL);


--
-- Name: uq_scaling_groups_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_scaling_groups_is_default ON public.scaling_groups USING btree (is_default) WHERE is_default;


--
-- Name: uq_ssh_keypairs_is_default; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_ssh_keypairs_is_default ON public.ssh_keypairs USING btree (user_id) WHERE is_default;


--
-- Name: uq_vfolder_auto_mounts_live_destination; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_vfolder_auto_mounts_live_destination ON public.vfolder_auto_mounts USING btree (scope_type, scope_id, mount_destination) WHERE (deleted_at IS NULL);


--
-- Name: uq_vfolder_auto_mounts_live_vfolder; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_vfolder_auto_mounts_live_vfolder ON public.vfolder_auto_mounts USING btree (scope_type, scope_id, vfolder_id) WHERE (deleted_at IS NULL);


--
-- Name: uq_vfolders_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_vfolders_project_name ON public.vfolders USING btree ("group", name) WHERE ((status)::text <> ALL ((ARRAY['delete-complete'::character varying, 'delete-error'::character varying])::text[]));


--
-- Name: agent_installed_images fk_agent_installed_images_agent_id_agents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_installed_images
    ADD CONSTRAINT fk_agent_installed_images_agent_id_agents FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: agent_installed_images fk_agent_installed_images_image_id_images; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_installed_images
    ADD CONSTRAINT fk_agent_installed_images_image_id_images FOREIGN KEY (image_id) REFERENCES public.images(id) ON DELETE CASCADE;


--
-- Name: agent_resources fk_agent_resources_agent_id_agents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_resources
    ADD CONSTRAINT fk_agent_resources_agent_id_agents FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: agent_resources fk_agent_resources_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_resources
    ADD CONSTRAINT fk_agent_resources_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: agents fk_agents_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT fk_agents_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id);


--
-- Name: agents fk_agents_scaling_group_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT fk_agents_scaling_group_scaling_groups FOREIGN KEY (scaling_group) REFERENCES public.scaling_groups(name);


--
-- Name: app_config_allow_list fk_app_config_allow_list_config_name_app_config_definitions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_allow_list
    ADD CONSTRAINT fk_app_config_allow_list_config_name_app_config_definitions FOREIGN KEY (config_name) REFERENCES public.app_config_definitions(config_name) ON DELETE CASCADE;


--
-- Name: app_config_fragments fk_app_config_fragments_config_name_scope_type; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_config_fragments
    ADD CONSTRAINT fk_app_config_fragments_config_name_scope_type FOREIGN KEY (config_name, scope_type) REFERENCES public.app_config_allow_list(config_name, scope_type) ON DELETE CASCADE;


--
-- Name: association_container_registries_groups fk_association_container_registries_groups_project_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_container_registries_groups
    ADD CONSTRAINT fk_association_container_registries_groups_project_id FOREIGN KEY (project_id) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: association_container_registries_groups fk_association_container_registries_groups_registry_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_container_registries_groups
    ADD CONSTRAINT fk_association_container_registries_groups_registry_id FOREIGN KEY (registry_id) REFERENCES public.container_registries(id) ON DELETE CASCADE;


--
-- Name: association_groups_users fk_association_groups_users_group_id_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_groups_users
    ADD CONSTRAINT fk_association_groups_users_group_id_groups FOREIGN KEY (group_id) REFERENCES public.groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: association_groups_users fk_association_groups_users_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.association_groups_users
    ADD CONSTRAINT fk_association_groups_users_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: audit_log_scopes fk_audit_log_scopes_audit_log_id_audit_logs; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log_scopes
    ADD CONSTRAINT fk_audit_log_scopes_audit_log_id_audit_logs FOREIGN KEY (audit_log_id) REFERENCES public.audit_logs(id) ON DELETE CASCADE;


--
-- Name: auto_generated_file_revisions fk_auto_generated_file_revisions_creator_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_file_revisions
    ADD CONSTRAINT fk_auto_generated_file_revisions_creator_id_users FOREIGN KEY (creator_id) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: auto_generated_file_revisions fk_auto_generated_file_revisions_file_id_auto_generated_files; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_file_revisions
    ADD CONSTRAINT fk_auto_generated_file_revisions_file_id_auto_generated_files FOREIGN KEY (file_id) REFERENCES public.auto_generated_files(id) ON DELETE CASCADE;


--
-- Name: auto_generated_files fk_auto_generated_files_entity_type_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auto_generated_files
    ADD CONSTRAINT fk_auto_generated_files_entity_type_virtual_entities FOREIGN KEY (entity_type, entity_id) REFERENCES public.virtual_entities(entity_type, entity_id) ON DELETE CASCADE;


--
-- Name: bootstrap_script_revisions fk_bootstrap_script_revisions_creator_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bootstrap_script_revisions
    ADD CONSTRAINT fk_bootstrap_script_revisions_creator_id_users FOREIGN KEY (creator_id) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: bootstrap_script_revisions fk_bootstrap_script_revisions_script_id_bootstrap_scripts; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bootstrap_script_revisions
    ADD CONSTRAINT fk_bootstrap_script_revisions_script_id_bootstrap_scripts FOREIGN KEY (script_id) REFERENCES public.bootstrap_scripts(id) ON DELETE CASCADE;


--
-- Name: deployment_designated_agents fk_deployment_designated_agents_agent_uuid_agents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_designated_agents
    ADD CONSTRAINT fk_deployment_designated_agents_agent_uuid_agents FOREIGN KEY (agent_uuid) REFERENCES public.agents(uuid) ON DELETE CASCADE;


--
-- Name: deployment_designated_agents fk_deployment_designated_agents_endpoint_id_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_designated_agents
    ADD CONSTRAINT fk_deployment_designated_agents_endpoint_id_endpoints FOREIGN KEY (endpoint_id) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: deployment_policies fk_deployment_policies_endpoint; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_policies
    ADD CONSTRAINT fk_deployment_policies_endpoint FOREIGN KEY (endpoint) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: deployment_revisions fk_deployment_revisions_endpoint_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT fk_deployment_revisions_endpoint_endpoints FOREIGN KEY (endpoint) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: deployment_revisions fk_deployment_revisions_image_images; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT fk_deployment_revisions_image_images FOREIGN KEY (image) REFERENCES public.images(id) ON DELETE SET NULL;


--
-- Name: deployment_revisions fk_deployment_revisions_model_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT fk_deployment_revisions_model_vfolders FOREIGN KEY (model) REFERENCES public.vfolders(id) ON DELETE SET NULL;


--
-- Name: deployment_revisions fk_deployment_revisions_revision_preset_id_deployment_r_ba4c; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT fk_deployment_revisions_revision_preset_id_deployment_r_ba4c FOREIGN KEY (revision_preset_id) REFERENCES public.deployment_revision_presets(id) ON DELETE SET NULL;


--
-- Name: deployment_revisions fk_deployment_revisions_runtime_variant_id_runtime_variants; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revisions
    ADD CONSTRAINT fk_deployment_revisions_runtime_variant_id_runtime_variants FOREIGN KEY (runtime_variant_id) REFERENCES public.runtime_variants(id) ON DELETE RESTRICT;


--
-- Name: domain_container_registry_relations fk_domain_container_registry_relations_container_registry_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_container_registry_relations
    ADD CONSTRAINT fk_domain_container_registry_relations_container_registry_id FOREIGN KEY (container_registry_id) REFERENCES public.container_registries(id) ON DELETE CASCADE;


--
-- Name: domain_container_registry_relations fk_domain_container_registry_relations_domain_id_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.domain_container_registry_relations
    ADD CONSTRAINT fk_domain_container_registry_relations_domain_id_domains FOREIGN KEY (domain_id) REFERENCES public.domains(id) ON DELETE CASCADE;


--
-- Name: deployment_revision_resource_slots fk_dr_resource_slots_revision_id_deployment_revisions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_resource_slots
    ADD CONSTRAINT fk_dr_resource_slots_revision_id_deployment_revisions FOREIGN KEY (revision_id) REFERENCES public.deployment_revisions(id) ON DELETE CASCADE;


--
-- Name: deployment_revision_resource_slots fk_dr_resource_slots_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_revision_resource_slots
    ADD CONSTRAINT fk_dr_resource_slots_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: endpoint_auto_scaling_rules fk_endpoint_auto_scaling_rules_endpoint_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_auto_scaling_rules
    ADD CONSTRAINT fk_endpoint_auto_scaling_rules_endpoint_endpoints FOREIGN KEY (endpoint) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: endpoint_auto_scaling_rules fk_endpoint_auto_scaling_rules_prometheus_query_preset__dc1c; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_auto_scaling_rules
    ADD CONSTRAINT fk_endpoint_auto_scaling_rules_prometheus_query_preset__dc1c FOREIGN KEY (prometheus_query_preset_id) REFERENCES public.prometheus_query_presets(id) ON DELETE SET NULL;


--
-- Name: endpoint_tokens fk_endpoint_tokens_domain_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_tokens
    ADD CONSTRAINT fk_endpoint_tokens_domain_domains FOREIGN KEY (domain) REFERENCES public.domains(name) ON DELETE CASCADE;


--
-- Name: endpoint_tokens fk_endpoint_tokens_endpoint_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_tokens
    ADD CONSTRAINT fk_endpoint_tokens_endpoint_endpoints FOREIGN KEY (endpoint) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: endpoint_tokens fk_endpoint_tokens_project_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoint_tokens
    ADD CONSTRAINT fk_endpoint_tokens_project_groups FOREIGN KEY (project) REFERENCES public.groups(id) ON DELETE CASCADE;


--
-- Name: endpoints fk_endpoints_domain_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT fk_endpoints_domain_domains FOREIGN KEY (domain) REFERENCES public.domains(name) ON DELETE RESTRICT;


--
-- Name: endpoints fk_endpoints_project_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT fk_endpoints_project_groups FOREIGN KEY (project) REFERENCES public.groups(id) ON DELETE RESTRICT;


--
-- Name: endpoints fk_endpoints_resource_group_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT fk_endpoints_resource_group_scaling_groups FOREIGN KEY (resource_group) REFERENCES public.scaling_groups(name) ON DELETE RESTRICT;


--
-- Name: entity_membership_caps fk_entity_membership_caps_membership_id_entity_memberships; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_membership_caps
    ADD CONSTRAINT fk_entity_membership_caps_membership_id_entity_memberships FOREIGN KEY (membership_id) REFERENCES public.entity_memberships(id) ON DELETE CASCADE;


--
-- Name: entity_membership_fields fk_entity_membership_fields_cap_id_entity_membership_caps; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_membership_fields
    ADD CONSTRAINT fk_entity_membership_fields_cap_id_entity_membership_caps FOREIGN KEY (cap_id) REFERENCES public.entity_membership_caps(id) ON DELETE CASCADE;


--
-- Name: entity_memberships fk_entity_memberships_member_entity_id_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_memberships
    ADD CONSTRAINT fk_entity_memberships_member_entity_id_virtual_entities FOREIGN KEY (member_entity_id) REFERENCES public.virtual_entities(id) ON DELETE CASCADE;


--
-- Name: entity_memberships fk_entity_memberships_virtual_entity_id_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_memberships
    ADD CONSTRAINT fk_entity_memberships_virtual_entity_id_virtual_entities FOREIGN KEY (virtual_entity_id) REFERENCES public.virtual_entities(id) ON DELETE CASCADE;


--
-- Name: entity_shares fk_entity_shares_sharer_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_shares
    ADD CONSTRAINT fk_entity_shares_sharer_user_id_users FOREIGN KEY (sharer_user_id) REFERENCES public.users(uuid) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: error_logs fk_error_logs_user_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.error_logs
    ADD CONSTRAINT fk_error_logs_user_users FOREIGN KEY ("user") REFERENCES public.users(uuid);


--
-- Name: groups fk_groups_creator_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT fk_groups_creator_id_users FOREIGN KEY (creator_id) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: groups fk_groups_domain_name_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT fk_groups_domain_name_domains FOREIGN KEY (domain_name) REFERENCES public.domains(name) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: groups fk_groups_resource_policy_project_resource_policies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT fk_groups_resource_policy_project_resource_policies FOREIGN KEY (resource_policy) REFERENCES public.project_resource_policies(name);


--
-- Name: idle_checker_bindings fk_idle_checker_bindings_idle_checker_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idle_checker_bindings
    ADD CONSTRAINT fk_idle_checker_bindings_idle_checker_id FOREIGN KEY (idle_checker_id) REFERENCES public.idle_checkers(id) ON DELETE CASCADE;


--
-- Name: image_aliases fk_image_aliases_image_images; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_aliases
    ADD CONSTRAINT fk_image_aliases_image_images FOREIGN KEY (image) REFERENCES public.images(id) ON DELETE CASCADE;


--
-- Name: images fk_images_creator_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.images
    ADD CONSTRAINT fk_images_creator_id_users FOREIGN KEY (creator_id) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: images fk_images_registry_id_container_registries; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.images
    ADD CONSTRAINT fk_images_registry_id_container_registries FOREIGN KEY (registry_id) REFERENCES public.container_registries(id) ON DELETE RESTRICT;


--
-- Name: kernel_group_environ fk_kernel_group_environ_kernel_group_id_kernel_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_environ
    ADD CONSTRAINT fk_kernel_group_environ_kernel_group_id_kernel_groups FOREIGN KEY (kernel_group_id) REFERENCES public.kernel_groups(id) ON DELETE CASCADE;


--
-- Name: kernel_group_resource_slots fk_kernel_group_resource_slots_kernel_group_id_kernel_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_resource_slots
    ADD CONSTRAINT fk_kernel_group_resource_slots_kernel_group_id_kernel_groups FOREIGN KEY (kernel_group_id) REFERENCES public.kernel_groups(id) ON DELETE RESTRICT;


--
-- Name: kernel_group_resource_slots fk_kernel_group_resource_slots_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_resource_slots
    ADD CONSTRAINT fk_kernel_group_resource_slots_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: kernel_group_vfolder_mounts fk_kernel_group_vfolder_mounts_kernel_group_id_kernel_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_vfolder_mounts
    ADD CONSTRAINT fk_kernel_group_vfolder_mounts_kernel_group_id_kernel_groups FOREIGN KEY (kernel_group_id) REFERENCES public.kernel_groups(id) ON DELETE CASCADE;


--
-- Name: kernel_group_vfolder_mounts fk_kernel_group_vfolder_mounts_vfolder_id_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_group_vfolder_mounts
    ADD CONSTRAINT fk_kernel_group_vfolder_mounts_vfolder_id_vfolders FOREIGN KEY (vfolder_id) REFERENCES public.vfolders(id) ON DELETE CASCADE;


--
-- Name: kernel_groups fk_kernel_groups_image_id_images; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_groups
    ADD CONSTRAINT fk_kernel_groups_image_id_images FOREIGN KEY (image_id) REFERENCES public.images(id) ON DELETE SET NULL;


--
-- Name: kernel_groups fk_kernel_groups_session_id_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernel_groups
    ADD CONSTRAINT fk_kernel_groups_session_id_sessions FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON DELETE CASCADE;


--
-- Name: kernels fk_kernels_agent_agents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_agent_agents FOREIGN KEY (agent) REFERENCES public.agents(id);


--
-- Name: kernels fk_kernels_domain_name_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_domain_name_domains FOREIGN KEY (domain_name) REFERENCES public.domains(name);


--
-- Name: kernels fk_kernels_group_id_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_group_id_groups FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: kernels fk_kernels_image_id_images; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_image_id_images FOREIGN KEY (image_id) REFERENCES public.images(id) ON DELETE SET NULL;


--
-- Name: kernels fk_kernels_kernel_group_id_kernel_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_kernel_group_id_kernel_groups FOREIGN KEY (kernel_group_id) REFERENCES public.kernel_groups(id) ON DELETE RESTRICT;


--
-- Name: kernels fk_kernels_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id);


--
-- Name: kernels fk_kernels_scaling_group_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_scaling_group_scaling_groups FOREIGN KEY (scaling_group) REFERENCES public.scaling_groups(name);


--
-- Name: kernels fk_kernels_session_id_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_session_id_sessions FOREIGN KEY (session_id) REFERENCES public.sessions(id);


--
-- Name: kernels fk_kernels_user_uuid_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.kernels
    ADD CONSTRAINT fk_kernels_user_uuid_users FOREIGN KEY (user_uuid) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: keypairs fk_keypairs_resource_policy_keypair_resource_policies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypairs
    ADD CONSTRAINT fk_keypairs_resource_policy_keypair_resource_policies FOREIGN KEY (resource_policy) REFERENCES public.keypair_resource_policies(name);


--
-- Name: keypairs fk_keypairs_user_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.keypairs
    ADD CONSTRAINT fk_keypairs_user_users FOREIGN KEY ("user") REFERENCES public.users(uuid);


--
-- Name: login_history fk_login_history_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT fk_login_history_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: login_sessions fk_login_sessions_login_client_type_id_login_client_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_sessions
    ADD CONSTRAINT fk_login_sessions_login_client_type_id_login_client_types FOREIGN KEY (login_client_type_id) REFERENCES public.login_client_types(id) ON DELETE SET NULL;


--
-- Name: login_sessions fk_login_sessions_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_sessions
    ADD CONSTRAINT fk_login_sessions_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: model_card_resource_requirements fk_mc_resource_req_model_card_id_model_cards; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_card_resource_requirements
    ADD CONSTRAINT fk_mc_resource_req_model_card_id_model_cards FOREIGN KEY (model_card_id) REFERENCES public.model_cards(id) ON DELETE CASCADE;


--
-- Name: model_card_resource_requirements fk_mc_resource_req_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_card_resource_requirements
    ADD CONSTRAINT fk_mc_resource_req_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: model_cards fk_model_cards_creator_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT fk_model_cards_creator_users FOREIGN KEY (creator) REFERENCES public.users(uuid) ON DELETE RESTRICT;


--
-- Name: model_cards fk_model_cards_domain_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT fk_model_cards_domain_domains FOREIGN KEY (domain) REFERENCES public.domains(name) ON DELETE RESTRICT;


--
-- Name: model_cards fk_model_cards_project_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT fk_model_cards_project_groups FOREIGN KEY (project) REFERENCES public.groups(id) ON DELETE RESTRICT;


--
-- Name: model_cards fk_model_cards_vfolder_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_cards
    ADD CONSTRAINT fk_model_cards_vfolder_vfolders FOREIGN KEY (vfolder) REFERENCES public.vfolders(id) ON DELETE RESTRICT;


--
-- Name: organization_auto_generated_file_relations fk_organization_auto_generated_file_relations_file_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_auto_generated_file_relations
    ADD CONSTRAINT fk_organization_auto_generated_file_relations_file_id FOREIGN KEY (file_id) REFERENCES public.auto_generated_files(id) ON DELETE CASCADE;


--
-- Name: organization_auto_generated_file_relations fk_organization_auto_generated_file_relations_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organization_auto_generated_file_relations
    ADD CONSTRAINT fk_organization_auto_generated_file_relations_virtual_entities FOREIGN KEY (organization_type, organization_id) REFERENCES public.virtual_entities(entity_type, entity_id) ON DELETE CASCADE;


--
-- Name: permission_fields fk_permission_fields_permission_id_permissions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permission_fields
    ADD CONSTRAINT fk_permission_fields_permission_id_permissions FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: permissions fk_permissions_role_id_roles; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT fk_permissions_role_id_roles FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: preset_resource_slots fk_preset_resource_slots_preset_id_drp; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preset_resource_slots
    ADD CONSTRAINT fk_preset_resource_slots_preset_id_drp FOREIGN KEY (preset_id) REFERENCES public.deployment_revision_presets(id) ON DELETE CASCADE;


--
-- Name: preset_resource_slots fk_preset_resource_slots_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.preset_resource_slots
    ADD CONSTRAINT fk_preset_resource_slots_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: prometheus_query_presets fk_prometheus_query_presets_category_id_prometheus_quer_8a51; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.prometheus_query_presets
    ADD CONSTRAINT fk_prometheus_query_presets_category_id_prometheus_quer_8a51 FOREIGN KEY (category_id) REFERENCES public.prometheus_query_preset_categories(id) ON DELETE SET NULL;


--
-- Name: replica_groups fk_replica_groups_deployment_id_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replica_groups
    ADD CONSTRAINT fk_replica_groups_deployment_id_endpoints FOREIGN KEY (deployment_id) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: replica_groups fk_replica_groups_session_group_id_session_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.replica_groups
    ADD CONSTRAINT fk_replica_groups_session_group_id_session_groups FOREIGN KEY (session_group_id) REFERENCES public.session_groups(id);


--
-- Name: resource_allocations fk_resource_allocations_kernel_id_kernels; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT fk_resource_allocations_kernel_id_kernels FOREIGN KEY (kernel_id) REFERENCES public.kernels(id) ON DELETE CASCADE;


--
-- Name: resource_allocations fk_resource_allocations_slot_name_resource_slot_types; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_allocations
    ADD CONSTRAINT fk_resource_allocations_slot_name_resource_slot_types FOREIGN KEY (slot_name) REFERENCES public.resource_slot_types(slot_name);


--
-- Name: resource_group_volume_offers fk_resource_group_volume_offers_resource_group_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_group_volume_offers
    ADD CONSTRAINT fk_resource_group_volume_offers_resource_group_id FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id) ON DELETE CASCADE;


--
-- Name: resource_group_volume_offers fk_resource_group_volume_offers_storage_volume_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_group_volume_offers
    ADD CONSTRAINT fk_resource_group_volume_offers_storage_volume_id FOREIGN KEY (storage_volume_id) REFERENCES public.storage_volumes(id) ON DELETE CASCADE;


--
-- Name: role_permission_presets fk_role_permission_presets_role_preset_id_role_presets; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permission_presets
    ADD CONSTRAINT fk_role_permission_presets_role_preset_id_role_presets FOREIGN KEY (role_preset_id) REFERENCES public.role_presets(id) ON DELETE CASCADE;


--
-- Name: roles fk_roles_role_preset_id_role_presets; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_role_preset_id_role_presets FOREIGN KEY (role_preset_id) REFERENCES public.role_presets(id) ON DELETE SET NULL;


--
-- Name: roles fk_roles_scope_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT fk_roles_scope_virtual_entities FOREIGN KEY (scope_type, scope_id) REFERENCES public.virtual_entities(entity_type, entity_id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;


--
-- Name: routings fk_routings_domain_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_domain_domains FOREIGN KEY (domain) REFERENCES public.domains(name) ON DELETE RESTRICT;


--
-- Name: routings fk_routings_endpoint_endpoints; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_endpoint_endpoints FOREIGN KEY (endpoint) REFERENCES public.endpoints(id) ON DELETE CASCADE;


--
-- Name: routings fk_routings_project_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_project_groups FOREIGN KEY (project) REFERENCES public.groups(id) ON DELETE RESTRICT;


--
-- Name: routings fk_routings_replica_group_id_replica_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_replica_group_id_replica_groups FOREIGN KEY (replica_group_id) REFERENCES public.replica_groups(id) ON DELETE SET NULL;


--
-- Name: routings fk_routings_session_owner_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_session_owner_users FOREIGN KEY (session_owner) REFERENCES public.users(uuid) ON DELETE RESTRICT;


--
-- Name: routings fk_routings_session_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routings
    ADD CONSTRAINT fk_routings_session_sessions FOREIGN KEY (session) REFERENCES public.sessions(id) ON DELETE RESTRICT;


--
-- Name: scope_bindings fk_scope_bindings_scope_entity_id_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scope_bindings
    ADD CONSTRAINT fk_scope_bindings_scope_entity_id_virtual_entities FOREIGN KEY (scope_entity_id) REFERENCES public.virtual_entities(id) ON DELETE CASCADE;


--
-- Name: scope_bindings fk_scope_bindings_virtual_entity_id_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scope_bindings
    ADD CONSTRAINT fk_scope_bindings_virtual_entity_id_virtual_entities FOREIGN KEY (virtual_entity_id) REFERENCES public.virtual_entities(id) ON DELETE CASCADE;


--
-- Name: service_catalog_endpoint fk_service_catalog_endpoint_service_id_service_catalog; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_catalog_endpoint
    ADD CONSTRAINT fk_service_catalog_endpoint_service_id_service_catalog FOREIGN KEY (service_id) REFERENCES public.service_catalog(id) ON DELETE CASCADE;


--
-- Name: service_storage_backend_status fk_service_storage_backend_status_service_catalog_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_storage_backend_status
    ADD CONSTRAINT fk_service_storage_backend_status_service_catalog_id FOREIGN KEY (service_catalog_id) REFERENCES public.service_catalog(id) ON DELETE CASCADE;


--
-- Name: service_storage_backend_status fk_service_storage_backend_status_storage_backend_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.service_storage_backend_status
    ADD CONSTRAINT fk_service_storage_backend_status_storage_backend_id FOREIGN KEY (storage_backend_id) REFERENCES public.storage_backends(id) ON DELETE CASCADE;


--
-- Name: session_dependencies fk_session_dependencies_depends_on_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_dependencies
    ADD CONSTRAINT fk_session_dependencies_depends_on_sessions FOREIGN KEY (depends_on) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: session_dependencies fk_session_dependencies_session_id_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_dependencies
    ADD CONSTRAINT fk_session_dependencies_session_id_sessions FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: session_designated_agents fk_session_designated_agents_agent_uuid_agents; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_designated_agents
    ADD CONSTRAINT fk_session_designated_agents_agent_uuid_agents FOREIGN KEY (agent_uuid) REFERENCES public.agents(uuid) ON DELETE CASCADE;


--
-- Name: session_designated_agents fk_session_designated_agents_session_id_sessions; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_designated_agents
    ADD CONSTRAINT fk_session_designated_agents_session_id_sessions FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON DELETE CASCADE;


--
-- Name: session_groups fk_session_groups_domain_id_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_groups
    ADD CONSTRAINT fk_session_groups_domain_id_domains FOREIGN KEY (domain_id) REFERENCES public.domains(id);


--
-- Name: session_groups fk_session_groups_owner_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_groups
    ADD CONSTRAINT fk_session_groups_owner_user_id_users FOREIGN KEY (owner_user_id) REFERENCES public.users(uuid) ON DELETE RESTRICT;


--
-- Name: session_groups fk_session_groups_project_id_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_groups
    ADD CONSTRAINT fk_session_groups_project_id_groups FOREIGN KEY (project_id) REFERENCES public.groups(id);


--
-- Name: session_idle_checks fk_session_idle_checks_idle_checker_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_idle_checks
    ADD CONSTRAINT fk_session_idle_checks_idle_checker_id FOREIGN KEY (idle_checker_id) REFERENCES public.idle_checkers(id) ON DELETE CASCADE;


--
-- Name: session_idle_checks fk_session_idle_checks_manually_triggered_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_idle_checks
    ADD CONSTRAINT fk_session_idle_checks_manually_triggered_by FOREIGN KEY (manually_triggered_by) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: session_idle_checks fk_session_idle_checks_session_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_idle_checks
    ADD CONSTRAINT fk_session_idle_checks_session_id FOREIGN KEY (session_id) REFERENCES public.sessions(id) ON DELETE CASCADE;


--
-- Name: session_templates fk_session_templates_domain_name_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_templates
    ADD CONSTRAINT fk_session_templates_domain_name_domains FOREIGN KEY (domain_name) REFERENCES public.domains(name);


--
-- Name: session_templates fk_session_templates_group_id_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_templates
    ADD CONSTRAINT fk_session_templates_group_id_groups FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: session_templates fk_session_templates_user_uuid_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.session_templates
    ADD CONSTRAINT fk_session_templates_user_uuid_users FOREIGN KEY (user_uuid) REFERENCES public.users(uuid);


--
-- Name: sessions fk_sessions_domain_id_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_domain_id_domains FOREIGN KEY (domain_id) REFERENCES public.domains(id);


--
-- Name: sessions fk_sessions_domain_name_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_domain_name_domains FOREIGN KEY (domain_name) REFERENCES public.domains(name);


--
-- Name: sessions fk_sessions_group_id_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_group_id_groups FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: sessions fk_sessions_replica_id_routings; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_replica_id_routings FOREIGN KEY (replica_id) REFERENCES public.routings(id) ON DELETE SET NULL;


--
-- Name: sessions fk_sessions_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id);


--
-- Name: sessions fk_sessions_scaling_group_name_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_scaling_group_name_scaling_groups FOREIGN KEY (scaling_group_name) REFERENCES public.scaling_groups(name);


--
-- Name: sessions fk_sessions_session_group_id_session_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_session_group_id_session_groups FOREIGN KEY (session_group_id) REFERENCES public.session_groups(id) ON DELETE SET NULL;


--
-- Name: sessions fk_sessions_user_uuid_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT fk_sessions_user_uuid_users FOREIGN KEY (user_uuid) REFERENCES public.users(uuid) ON DELETE SET NULL;


--
-- Name: sgroups_for_domains fk_sgroups_for_domains_domain_id_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_domains
    ADD CONSTRAINT fk_sgroups_for_domains_domain_id_domains FOREIGN KEY (domain_id) REFERENCES public.domains(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sgroups_for_domains fk_sgroups_for_domains_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_domains
    ADD CONSTRAINT fk_sgroups_for_domains_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sgroups_for_groups fk_sgroups_for_groups_group_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_groups
    ADD CONSTRAINT fk_sgroups_for_groups_group_groups FOREIGN KEY ("group") REFERENCES public.groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sgroups_for_groups fk_sgroups_for_groups_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_groups
    ADD CONSTRAINT fk_sgroups_for_groups_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sgroups_for_keypairs fk_sgroups_for_keypairs_access_key_keypairs; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_keypairs
    ADD CONSTRAINT fk_sgroups_for_keypairs_access_key_keypairs FOREIGN KEY (access_key) REFERENCES public.keypairs(access_key) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: sgroups_for_keypairs fk_sgroups_for_keypairs_resource_group_id_scaling_groups; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sgroups_for_keypairs
    ADD CONSTRAINT fk_sgroups_for_keypairs_resource_group_id_scaling_groups FOREIGN KEY (resource_group_id) REFERENCES public.scaling_groups(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: ssh_keypairs fk_ssh_keypairs_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ssh_keypairs
    ADD CONSTRAINT fk_ssh_keypairs_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: storage_backends fk_storage_backends_storage_backend_type_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_backends
    ADD CONSTRAINT fk_storage_backends_storage_backend_type_id FOREIGN KEY (storage_backend_type_id) REFERENCES public.storage_backend_types(id) ON DELETE RESTRICT;


--
-- Name: storage_volume_service_holdings fk_storage_volume_service_holdings_service_catalog_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volume_service_holdings
    ADD CONSTRAINT fk_storage_volume_service_holdings_service_catalog_id FOREIGN KEY (service_catalog_id) REFERENCES public.service_catalog(id) ON DELETE CASCADE;


--
-- Name: storage_volume_service_holdings fk_storage_volume_service_holdings_storage_volume_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volume_service_holdings
    ADD CONSTRAINT fk_storage_volume_service_holdings_storage_volume_id FOREIGN KEY (storage_volume_id) REFERENCES public.storage_volumes(id) ON DELETE CASCADE;


--
-- Name: storage_volumes fk_storage_volumes_storage_backend_id_storage_backends; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.storage_volumes
    ADD CONSTRAINT fk_storage_volumes_storage_backend_id_storage_backends FOREIGN KEY (storage_backend_id) REFERENCES public.storage_backends(id) ON DELETE RESTRICT;


--
-- Name: user_default_bootstrap_scripts fk_user_default_bootstrap_scripts_script_id_bootstrap_scripts; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_default_bootstrap_scripts
    ADD CONSTRAINT fk_user_default_bootstrap_scripts_script_id_bootstrap_scripts FOREIGN KEY (script_id) REFERENCES public.bootstrap_scripts(id) ON DELETE CASCADE;


--
-- Name: user_default_bootstrap_scripts fk_user_default_bootstrap_scripts_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_default_bootstrap_scripts
    ADD CONSTRAINT fk_user_default_bootstrap_scripts_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: user_roles fk_user_roles_role_id_roles; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user_roles_role_id_roles FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles fk_user_roles_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user_roles_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: users fk_users_domain_id_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_domain_id_domains FOREIGN KEY (domain_id) REFERENCES public.domains(id);


--
-- Name: users fk_users_domain_name_domains; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_domain_name_domains FOREIGN KEY (domain_name) REFERENCES public.domains(name);


--
-- Name: users fk_users_resource_policy_user_resource_policies; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT fk_users_resource_policy_user_resource_policies FOREIGN KEY (resource_policy) REFERENCES public.user_resource_policies(name);


--
-- Name: vfolder_attachment fk_vfolder_attachment_kernel_kernels; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_attachment
    ADD CONSTRAINT fk_vfolder_attachment_kernel_kernels FOREIGN KEY (kernel) REFERENCES public.kernels(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vfolder_attachment fk_vfolder_attachment_vfolder_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_attachment
    ADD CONSTRAINT fk_vfolder_attachment_vfolder_vfolders FOREIGN KEY (vfolder) REFERENCES public.vfolders(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: vfolder_auto_mounts fk_vfolder_auto_mounts_scope_type_virtual_entities; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_auto_mounts
    ADD CONSTRAINT fk_vfolder_auto_mounts_scope_type_virtual_entities FOREIGN KEY (scope_type, scope_id) REFERENCES public.virtual_entities(entity_type, entity_id) ON DELETE CASCADE;


--
-- Name: vfolder_auto_mounts fk_vfolder_auto_mounts_vfolder_id_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_auto_mounts
    ADD CONSTRAINT fk_vfolder_auto_mounts_vfolder_id_vfolders FOREIGN KEY (vfolder_id) REFERENCES public.vfolders(id) ON DELETE CASCADE;


--
-- Name: vfolder_user_mount_policies fk_vfolder_user_mount_policies_user_id_users; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_user_mount_policies
    ADD CONSTRAINT fk_vfolder_user_mount_policies_user_id_users FOREIGN KEY (user_id) REFERENCES public.users(uuid) ON DELETE CASCADE;


--
-- Name: vfolder_user_mount_policies fk_vfolder_user_mount_policies_vfolder_id_vfolders; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolder_user_mount_policies
    ADD CONSTRAINT fk_vfolder_user_mount_policies_vfolder_id_vfolders FOREIGN KEY (vfolder_id) REFERENCES public.vfolders(id) ON DELETE CASCADE;


--
-- Name: vfolders fk_vfolders_storage_volume_id_storage_volumes; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vfolders
    ADD CONSTRAINT fk_vfolders_storage_volume_id_storage_volumes FOREIGN KEY (storage_volume_id) REFERENCES public.storage_volumes(id) ON DELETE RESTRICT;


--
-- Name: entity_shares recipient; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_shares
    ADD CONSTRAINT recipient FOREIGN KEY (recipient_entity_type, recipient_entity_id) REFERENCES public.virtual_entities(entity_type, entity_id) MATCH FULL ON DELETE CASCADE;


--
-- Name: entity_shares target; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_shares
    ADD CONSTRAINT target FOREIGN KEY (target_entity_type, target_entity_id) REFERENCES public.virtual_entities(entity_type, entity_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

