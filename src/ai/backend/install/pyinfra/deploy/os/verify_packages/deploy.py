"""Offline package repository verification (Phase 0 pre-flight check).

Performs HTTP HEAD checks against artifact URLs served at ``repo_url``
to verify that all required packages are accessible before deployment
begins.  Artifacts whose service is not placed (per the host's service
placement configuration) are skipped.
"""

from __future__ import annotations

import importlib.util
import shlex
from pathlib import Path
from typing import Any

from pyinfra import host
from pyinfra.operations import server

from ai.backend.install.pyinfra.runner import BaseDeploy

# Load manifest.py via file path — relative imports are not available
# because pyinfra loads deploy scripts via exec(), not standard import.
_manifest_path = Path(__file__).with_name("manifest.py")
_manifest_spec = importlib.util.spec_from_file_location("manifest", _manifest_path)
if _manifest_spec is None or _manifest_spec.loader is None:
    raise ImportError(
        f"Could not load manifest module from {_manifest_path}. "
        f"Verify the file exists and is a valid Python module."
    )
_manifest = importlib.util.module_from_spec(_manifest_spec)
_manifest_spec.loader.exec_module(_manifest)
ARTIFACT_CATEGORIES = _manifest.ARTIFACT_CATEGORIES
build_artifact_urls = _manifest.build_artifact_urls
filter_artifacts_by_placement = _manifest.filter_artifacts_by_placement


class VerifyPackagesDeploy(BaseDeploy):
    """Pre-flight check: verify that offline package artifacts are accessible."""

    _REQUIRED_HOST_DATA = ("bai_offline_repo_url", "bai_default_versions", "bai_service_placement")

    def __init__(self, host_data: Any) -> None:
        super().__init__()
        missing = [attr for attr in self._REQUIRED_HOST_DATA if not hasattr(host_data, attr)]
        if missing:
            raise RuntimeError(
                f"Verify packages deploy requires host data fields {missing} "
                f"that are only set for management nodes via inventory_base.py."
            )
        self.repo_url: str = host_data.bai_offline_repo_url
        self.versions: dict[str, str] = dict(host_data.bai_default_versions)
        self.service_placement: dict[str, list[str]] = dict(host_data.bai_service_placement)

    def install(self) -> None:
        artifact_urls = build_artifact_urls(self.repo_url, self.versions)
        required_keys = filter_artifacts_by_placement(self.service_placement)

        # Build a single shell script that checks all URLs and reports results.
        check_lines: list[str] = [
            "FAIL=0",
        ]
        for category, keys in ARTIFACT_CATEGORIES.items():
            category_keys = [k for k in keys if k in required_keys]
            if not category_keys:
                continue
            check_lines.append(f'echo "--- {category} ---"')
            for key in category_keys:
                url = artifact_urls[key]
                quoted_url = shlex.quote(url)
                check_lines.append(
                    f"HTTP_CODE=$(curl -sS --head --max-time 10 -o /dev/null "
                    f"-w '%{{http_code}}' {quoted_url} 2>/dev/null); "
                    f'if [ "$HTTP_CODE" -ge 200 ] 2>/dev/null && [ "$HTTP_CODE" -lt 400 ] 2>/dev/null; then '
                    f'echo "  OK  {key}"; '
                    f'elif [ "$HTTP_CODE" = "000" ]; then '
                    f'echo "  MISSING  {key}  (connection failed)  "{quoted_url}; FAIL=1; '
                    f"else "
                    f'echo "  MISSING  {key}  (HTTP $HTTP_CODE)  "{quoted_url}; FAIL=1; '
                    f"fi"
                )
        check_lines.append('if [ "$FAIL" -eq 1 ]; then')
        check_lines.append('  echo "FAILED: one or more artifacts are missing"')
        check_lines.append("  exit 1")
        check_lines.append("fi")
        check_lines.append('echo "All required artifacts are accessible"')

        # Joined as a single command so the $FAIL variable persists
        # across all curl checks (separate commands would each run in
        # their own shell invocation, resetting shell state).
        server.shell(
            name="Verify offline package artifacts",
            commands=["\n".join(check_lines)],
        )

    def remove(self) -> None:
        pass  # nothing to remove

    def update(self) -> None:
        self.install()


def main() -> None:
    deploy_mode = host.data.get("mode", "install")
    VerifyPackagesDeploy(host.data).run(deploy_mode)


main()
