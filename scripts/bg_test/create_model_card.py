"""Create a model VFolder and a model card pointing at it.

Defaults only — no CLI arguments. Run with `python3 create_model_card.py`.

Prints `<model_card_id> <vfolder_id>` to stdout so the caller can feed the
IDs back into manual delete tests (e.g. `adminDeleteModelCardV2(id, options)`).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

from _common import REPO, check_errors, decode_relay_id, gql

# A MODEL_STORE-type project is required for the model card.
# Look up via: SELECT id, name FROM groups WHERE type = 'model-store';
DEFAULT_MODEL_STORE_PROJECT_ID = "8e32dd28-d319-4e3b-8851-ea37837699a5"


def create_model_vfolder(name: str, project_id: str) -> str:
    """Create a model-usage VFolder owned by the given project and return its UUID.

    Storage-proxy host ACLs require model-usage vfolders to be project-owned
    (MODEL_STORE), not user-owned — otherwise the create returns 403.
    """
    cmd = [
        "./bai", "vfolder", "create",
        "--name", name,
        "--usage-mode", "model",
        "--group", project_id,
    ]
    print(f"$ (cwd={REPO}) {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=REPO, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"vfolder create failed: {result.stderr[-2000:]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"vfolder create returned non-JSON: {result.stdout[-2000:]}")
    return payload["vfolder"]["id"]


def main() -> None:
    suffix = int(time.time())
    vfolder_name = f"e2e-model-card-vf-{suffix}"
    card_name = f"e2e-model-card-{suffix}"

    vfolder_id = create_model_vfolder(vfolder_name, DEFAULT_MODEL_STORE_PROJECT_ID)
    print(f"Created vfolder: {vfolder_id} (name={vfolder_name})", file=sys.stderr)

    result = gql(f'''mutation {{
      adminCreateModelCardV2(input: {{
        name: "{card_name}"
        vfolderId: "{vfolder_id}"
        modelStoreProjectId: "{DEFAULT_MODEL_STORE_PROJECT_ID}"
        title: "E2E test card"
        description: "Disposable model card created by create_model_card.py"
      }}) {{
        modelCard {{ id }}
      }}
    }}''')

    data = check_errors(result, "adminCreateModelCardV2")
    relay_id = data["adminCreateModelCardV2"]["modelCard"]["id"]
    card_id = decode_relay_id(relay_id)

    print(f"Created model card: {card_id} (name={card_name})", file=sys.stderr)
    print(f"  vfolder_id: {vfolder_id}", file=sys.stderr)
    print()
    print(f"To delete the card and trash its vfolder, run:", file=sys.stderr)
    print(
        f'  ./bai gql --v2 \'mutation {{ adminDeleteModelCardV2('
        f'id: "{card_id}", options: {{ deleteAssociatedVfolder: true }}) '
        f'{{ id }} }}\'',
        file=sys.stderr,
    )

    print(f"{card_id} {vfolder_id}")


if __name__ == "__main__":
    main()
