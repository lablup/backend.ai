from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa

from ai.backend.manager.models.deployment_revision_preset.conditions import (
    DeploymentRevisionPresetConditions,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow


class TestByModelCardCompatible:
    def test_builds_relational_division_over_resource_slots(self) -> None:
        card_id = uuid4()
        condition = DeploymentRevisionPresetConditions.by_model_card_compatible(card_id)
        query = sa.select(DeploymentRevisionPresetRow.id).where(condition())

        # Compile without literal binds — the model card id stays a bind parameter
        # (a raw UUID has no literal renderer), while the structural column-to-column
        # predicates render in full.
        sql = str(query.compile())

        # Relational division renders as two nested EXISTS (outer negation over the
        # requirements, inner over the satisfying preset slots).
        assert sql.count("EXISTS") == 2
        assert "NOT" in sql
        # The card's requirements are the ones being divided over.
        assert "model_card_resource_requirements.model_card_id =" in sql
        # The inner sub-EXISTS correlates against BOTH the outer preset and the
        # requirement — otherwise the predicate degenerates into a cartesian match.
        assert "preset_resource_slots.preset_id = deployment_revision_presets.id" in sql
        assert "preset_resource_slots.slot_name = model_card_resource_requirements.slot_name" in sql
        assert (
            "preset_resource_slots.quantity >= model_card_resource_requirements.min_quantity" in sql
        )
        # Correlated, not a cartesian product pulled into the outer FROM.
        assert "FROM deployment_revision_presets, model_card_resource_requirements" not in sql
