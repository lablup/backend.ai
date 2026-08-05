from __future__ import annotations

from typing import Any

from ai.backend.manager.models.scaling_group.types import (
    CAPABILITY_DISCLOSURE,
    METADATA_EGRESS_DISCLOSURE,
    NONCE_RESIDUAL_DISCLOSURE,
    ConfidentialScalingGroupOpts,
)


def confidential_capability_view(opts: ConfidentialScalingGroupOpts | None) -> dict[str, Any]:
    opts = opts or ConfidentialScalingGroupOpts()
    return {
        "enabled": opts.enabled,
        "confidential_capable": opts.confidential_capable,
        "broker_endpoint": opts.broker_endpoint,
        "shim_public_addr": opts.shim_public_addr,
        "provisioning_record": opts.provisioning_record,
        "insecure_development": opts.insecure_development,
        "tcb_grace_period_seconds": opts.tcb_grace_period.total_seconds(),
        "admission_limit_per_image": opts.admission_limit_per_image,
        "metadata_egress_disclosure": METADATA_EGRESS_DISCLOSURE,
        "capability_provenance": "operator-declared",
        "capability_disclosure": CAPABILITY_DISCLOSURE,
        "nonce_residual_disclosure": NONCE_RESIDUAL_DISCLOSURE,
    }
