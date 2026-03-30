from pathlib import Path

# Common directory paths
SERVICE_DIR = "{home_dir}/appproxy"
WORKER_DIR_TEMPLATE = "{service_dir}/worker-{worker_type}"
COORDINATOR_DIR = "{service_dir}/coordinator"
TRAEFIK_DIR = "{service_dir}/traefik"

# Worker types
WORKER_TYPES = ["interactive", "inference", "tcp"]


def create_worker_configs(service_dir: Path, config: object) -> dict[str, dict]:
    """Create configurations for all worker types."""
    worker_configs = {}
    for worker_type in WORKER_TYPES:
        worker_dir = Path(
            WORKER_DIR_TEMPLATE.format(service_dir=service_dir, worker_type=worker_type)
        )
        worker_configs[worker_type] = {
            "dir": worker_dir,
            "advertised_hostname": getattr(config, f"worker_{worker_type}_advertised_hostname"),
            "port": getattr(config, f"worker_{worker_type}_port"),
            "authority": f"worker-{config.worker_node_number}-{worker_type}",
            "aiomonitor_termui_port": getattr(
                config, f"worker_{worker_type}_aiomonitor_termui_port"
            ),
            "aiomonitor_webui_port": getattr(config, f"worker_{worker_type}_aiomonitor_webui_port"),
            "protocol": "tcp" if worker_type == "tcp" else "http",
            "accepted_traffic": "inference" if worker_type == "inference" else "interactive",
            "app_port_start": getattr(config, f"worker_{worker_type}_app_port_start"),
            "app_port_end": getattr(config, f"worker_{worker_type}_app_port_end"),
            "traefik_api_port": getattr(
                config,
                f"worker_{worker_type}_traefik_api_port",
                9090 + WORKER_TYPES.index(worker_type),
            ),
            "service_name": f"appproxy-worker-{worker_type}",
            "run_script_name": f"run-appproxy-worker-{worker_type}.sh",
        }
    return worker_configs


def create_worker_config(service_dir: Path, config: object, worker_type: str) -> dict:
    """Create configuration for a specific worker type."""
    all_configs = create_worker_configs(service_dir, config)
    return all_configs[worker_type]
