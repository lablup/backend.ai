import json
import tempfile
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

from ai.backend.install.pyinfra.runner import BaseDockerComposeDeploy


class GrafanaDeploy(BaseDockerComposeDeploy):
    def __init__(self, host_data: object) -> None:
        super().__init__()
        self.home_dir = host_data.bai_home_dir
        self.user = host_data.bai_user
        self.service_name = "grafana"
        self.service_home = Path(f"{self.home_dir}/dashboard/grafana")
        self.service_dir = self.service_home

        self.config = host_data.services["grafana"]
        self.data_sources_config = host_data.services["data_sources"]
        self.services = host_data.services

        # Set data_dir: use config value if provided, otherwise default to {home_dir}/.data/grafana
        self.data_dir = self.config.data_dir or f"{self.home_dir}/.data/grafana"

        # Fixed datasource UIDs (stable across re-deployments)
        self.prometheus_uid = "bai-prometheus"
        self.pyroscope_uid = "bai-pyroscope"
        self.loki_uid = "bai-loki"
        self.tempo_uid = "bai-tempo"
        self.postgres_core_uid = "bai-core-db"
        self.postgres_cp_uid = "bai-cp-db"

    def create_datasources_yml(self) -> None:
        files.template(
            name="Create datasources.yml",
            src=str(Path(__file__).parent / "templates/datasources.yml.j2"),
            dest=f"{self.service_home}/provisioning/datasources/datasources.yml",
            user=self.user,
            mode="644",
            # Jinja2 context (resolve host.docker.internal to actual host IP)
            prometheus_host=self.resolve_host(self.data_sources_config.prometheus_host),
            prometheus_port=self.data_sources_config.prometheus_port,
            prometheus_uid=self.prometheus_uid,
            pyroscope_host=self.resolve_host(self.data_sources_config.pyroscope_host),
            pyroscope_port=self.data_sources_config.pyroscope_port,
            pyroscope_uid=self.pyroscope_uid,
            loki_host=self.resolve_host(self.data_sources_config.loki_host),
            loki_port=self.data_sources_config.loki_port,
            loki_uid=self.loki_uid,
            tempo_host=self.resolve_host(self.data_sources_config.tempo_host),
            tempo_port=self.data_sources_config.tempo_port,
            tempo_uid=self.tempo_uid,
            # PostgreSQL datasource (both core and CP use the same database)
            postgres_host=self.resolve_host(self.data_sources_config.postgres_host),
            postgres_port=self.data_sources_config.postgres_port,
            postgres_database=self.data_sources_config.postgres_database,
            postgres_user=self.data_sources_config.postgres_user,
            postgres_password=self.data_sources_config.postgres_password,
            postgres_core_uid=self.postgres_core_uid,
            postgres_cp_uid=self.postgres_cp_uid,
        )

    def create_dashboards_yml(self) -> None:
        files.template(
            name="Create dashboards.yml",
            src=str(Path(__file__).parent / "templates/dashboards.yml.j2"),
            dest=f"{self.service_home}/provisioning/dashboards/dashboards.yml",
            user=self.user,
            mode="644",
        )

    def create_alerting_provisioning(self) -> None:
        """Deploy Grafana alert rule provisioning file.

        Alert rules are always deployed regardless of SMTP configuration,
        so firing state is visible in the Grafana UI even without notifications.
        """
        files.template(
            name="Create alert_rules.yml",
            src=str(Path(__file__).parent / "templates/alert_rules.yml.j2"),
            dest=f"{self.service_home}/provisioning/alerting/alert_rules.yml",
            user=self.user,
            mode="644",
            prometheus_uid=self.prometheus_uid,
        )

    def fix_service_home_ownership(self) -> None:
        """Ensure service_home files are owned by bai user before file operations.

        Previous deployments by root can leave files with root:root ownership,
        which blocks subsequent SFTP overwrites by the bai user.
        """
        server.shell(
            name="Fix service home file ownership for SFTP uploads",
            commands=[
                f"chown -R {self.user}:{self.user} {self.service_home}",
            ],
            _sudo=True,
        )

    def copy_additional_dashboards(self) -> None:
        """Copy additional dashboard JSON files from templates/dashboards"""
        # Source directory for dashboard files (within templates)
        dashboard_source_dir = Path(__file__).parent / "templates/dashboards"

        if not dashboard_source_dir.exists():
            return

        # Common dashboards deployed for all configurations
        dashboard_files = [
            "backend-ai-service-group-dashboard.json",
            # TODO: Refactor backend-ai-overall-resource-usages.json
            #   - CP DB panels (agent_agentmetric, session_computesessionmetric) need
            #     a separate Control Panel database connection (not same as Core DB)
            #   - GPU utilization panels from CP DB duplicate the DCGM-based gpu-usage-dashboard
            #   - VAR_TOTAL_GPU_COUNT / VAR_GPU_COUNT_PER_NODE constants from __inputs
            #     are not resolved at provisioning time (need explicit replacement in deploy code)
            #   - Consider splitting into Core-only version (session/allocation trends)
            #     and CP-dependent version (per-session GPU utilization)
            "backend-ai-logs.json",
            "appproxy-traefik-dashboard.json",
            "gpu-usage-dashboard.json",
            "postgresql-database.json",
            "redis-dashboard.json",
            "prometheus-stats.json",
            "blackbox-exporter.json",
        ]

        # HA-only dashboards: deploy only when the corresponding HA service is configured
        if "etcd_ha" in self.services:
            dashboard_files.append("etcd-clusters.json")
        if "postgres_ha" in self.services:
            dashboard_files.append("postgresql-patroni.json")
        if "redis_ha" in self.services:
            dashboard_files.append("redis-cluster.json")

        # Datasource UID mapping for dashboard provisioning
        datasource_mapping = {
            "DS_PROMETHEUS": self.prometheus_uid,
            "DS_LOKI": self.loki_uid,
            "DS_DB_- CORE": self.postgres_core_uid,
            "DS_DB_- CONTROL PANEL": self.postgres_cp_uid,
        }

        for dashboard_file in dashboard_files:
            source_path = dashboard_source_dir / dashboard_file
            if not source_path.exists():
                continue

            # Read dashboard JSON
            with Path(source_path).open() as f:
                dashboard_data = json.load(f)

            # Update datasource UIDs in the dashboard
            dashboard_json = json.dumps(dashboard_data)
            for old_uid, new_uid in datasource_mapping.items():
                dashboard_json = dashboard_json.replace(f'"${{{old_uid}}}"', f'"{new_uid}"')
                dashboard_json = dashboard_json.replace(
                    f'"uid": "{old_uid}"', f'"uid": "{new_uid}"'
                )

            # Remove __inputs section as datasources are provisioned
            dashboard_data = json.loads(dashboard_json)
            if "__inputs" in dashboard_data:
                del dashboard_data["__inputs"]
            if "id" in dashboard_data:
                dashboard_data["id"] = None

            # Create a fixed temporary directory for dashboard files
            # Using fixed paths prevents accumulation of temp files on repeated deployments
            tmp_dir = Path(tempfile.gettempdir()) / "grafana-dashboards-pyinfra"
            tmp_dir.mkdir(exist_ok=True)
            tmp_file_path = tmp_dir / dashboard_file

            # Write the modified dashboard to the temporary file
            with Path(tmp_file_path).open("w") as f:
                json.dump(dashboard_data, f, indent=2)

            # Copy the modified dashboard to remote server
            dest_path = f"{self.service_home}/dashboards/{dashboard_file}"
            files.put(
                name=f"Deploy dashboard: {dashboard_file}",
                src=str(tmp_file_path),
                dest=dest_path,
                user=self.user,
                mode="644",
                create_remote_dir=False,
            )

    def change_permissions(self) -> None:
        """Set permissions for Grafana data directory (Grafana uses UID 472)"""
        data_dir = self.data_dir
        server.shell(
            name="Set grafana data directory permissions for grafana user (472:472)",
            commands=[
                # Ensure directory exists
                f"mkdir -p {data_dir}",
                # Set ownership to grafana user (472:472) - force if needed
                f"chown -R 472:472 {data_dir} || echo 'Failed to change ownership, continuing...'",
                # Set appropriate permissions for grafana user
                f"chmod -R 755 {data_dir}",
            ],
            _sudo=True,
        )

    def install(self) -> None:
        smtp = self.config.smtp
        smtp_enabled = smtp is not None and smtp.enabled

        self.create_directories([
            self.service_home,
            self.service_home / "provisioning",
            self.service_home / "provisioning" / "datasources",
            self.service_home / "provisioning" / "dashboards",
            self.service_home / "provisioning" / "alerting",
            self.service_home / "dashboards",
            self.data_dir,
        ])
        self.fix_service_home_ownership()
        smtp_vars = (
            {f"smtp_{k}": v for k, v in smtp.model_dump(exclude={"enabled"}).items()}
            if smtp_enabled
            else {}
        )
        self.create_env_file(
            template_name=".env.j2",
            user=self.user,
            mode="644",
            grafana_image_tag=self.config.grafana_image_tag,
            grafana_port=self.config.port,
            grafana_admin_id=self.config.admin_id,
            grafana_admin_password=self.config.admin_password,
            smtp_enabled=smtp_enabled,
            **smtp_vars,
        )
        self.create_datasources_yml()
        self.create_dashboards_yml()
        self.create_alerting_provisioning()
        self.copy_additional_dashboards()
        self.create_docker_compose_yaml(
            template_name="docker-compose.yml.j2",
            user=self.user,
            mode="644",
            data_dir=self.data_dir,
            smtp_enabled=smtp_enabled,
        )
        self.create_service_manage_scripts()
        self.change_permissions()
        self.load_image()
        self.start_service()

    def remove(self) -> None:
        # Check if service directory exists before stopping
        server.shell(
            name="Stop Grafana service if directory exists",
            commands=[
                f"[ -d {self.service_home} ] && cd {self.service_home} && docker compose down || true",
            ],
        )
        self.remove_directories([self.data_dir, self.service_home])


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    deploy = GrafanaDeploy(host.data)

    if deploy_mode == "remove":
        deploy.remove()
    else:
        deploy.install()


main()
