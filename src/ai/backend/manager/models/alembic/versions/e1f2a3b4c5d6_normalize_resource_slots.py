"""normalize resource slots for model cards, presets, and revisions

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-04-03

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create model_card_resource_requirements
    op.create_table(
        "model_card_resource_requirements",
        sa.Column("model_card_id", sa.Uuid(), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("min_quantity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("model_card_id", "slot_name"),
        sa.ForeignKeyConstraint(
            ["model_card_id"],
            ["model_cards.id"],
            name="fk_mc_resource_req_model_card_id_model_cards",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_mc_resource_req_slot_name_resource_slot_types",
        ),
    )
    op.create_index(
        "ix_mc_resource_req_slot_name",
        "model_card_resource_requirements",
        ["slot_name"],
    )

    # 2. Create preset_resource_slots
    op.create_table(
        "preset_resource_slots",
        sa.Column("preset_id", sa.Uuid(), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("preset_id", "slot_name"),
        sa.ForeignKeyConstraint(
            ["preset_id"],
            ["deployment_revision_presets.id"],
            name="fk_preset_resource_slots_preset_id_drp",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_preset_resource_slots_slot_name_resource_slot_types",
        ),
    )
    op.create_index(
        "ix_preset_resource_slots_slot_name",
        "preset_resource_slots",
        ["slot_name"],
    )

    # 3. Create deployment_revision_resource_slots
    op.create_table(
        "deployment_revision_resource_slots",
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("slot_name", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("revision_id", "slot_name"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["deployment_revisions.id"],
            name="fk_dr_resource_slots_revision_id_deployment_revisions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_dr_resource_slots_slot_name_resource_slot_types",
        ),
    )
    op.create_index(
        "ix_dr_resource_slots_slot_name",
        "deployment_revision_resource_slots",
        ["slot_name"],
    )

    # 4. Create a temporary helper to parse BinarySize-suffixed strings
    #    (e.g. "32g" → 34359738368, "4m" → 4194304, plain "1" → 1).
    conn = op.get_bind()
    conn.execute(
        sa.text("""
        CREATE OR REPLACE FUNCTION _tmp_parse_binary_size(val text)
        RETURNS numeric(24, 6) AS $$
        DECLARE
            cleaned text;
            suffix  char;
            num_part text;
            multiplier numeric;
        BEGIN
            cleaned := lower(trim(val));
            -- Fast path: try direct numeric cast
            BEGIN
                RETURN cleaned::numeric(24, 6);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END;
            -- Strip known binary-size endings (order matters: longest first)
            cleaned := regexp_replace(cleaned, '(ibytes|ibyte|ib|bytes|byte|b)$', '');
            -- If trailing letter is a known suffix, split
            IF cleaned ~ '[a-z]$' THEN
                suffix   := right(cleaned, 1);
                num_part := left(cleaned, length(cleaned) - 1);
            ELSE
                RETURN cleaned::numeric(24, 6);
            END IF;
            multiplier := CASE suffix
                WHEN 'k' THEN 1024                    -- 2^10
                WHEN 'm' THEN 1048576                  -- 2^20
                WHEN 'g' THEN 1073741824               -- 2^30
                WHEN 't' THEN 1099511627776            -- 2^40
                WHEN 'p' THEN 1125899906842624         -- 2^50
                WHEN 'e' THEN 1152921504606846976      -- 2^60
                ELSE NULL
            END;
            IF multiplier IS NULL THEN
                RAISE EXCEPTION 'Unknown BinarySize suffix in value: %', val;
            END IF;
            RETURN (num_part::numeric * multiplier)::numeric(24, 6);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """)
    )

    # From model_cards.min_resource
    conn.execute(
        sa.text("""
        INSERT INTO resource_slot_types (slot_name, slot_type, rank)
        SELECT DISTINCT kv.key, 'count', 0
        FROM model_cards mc, jsonb_each_text(mc.min_resource -> 'slots') AS kv(key, value)
        WHERE mc.min_resource IS NOT NULL
          AND kv.key NOT IN (SELECT slot_name FROM resource_slot_types)
        ON CONFLICT DO NOTHING
    """)
    )

    # From deployment_revision_presets.resource_slots
    conn.execute(
        sa.text("""
        INSERT INTO resource_slot_types (slot_name, slot_type, rank)
        SELECT DISTINCT elem ->> 'resource_type', 'count', 0
        FROM deployment_revision_presets p,
             jsonb_array_elements(p.resource_slots) AS elem
        WHERE p.resource_slots IS NOT NULL
          AND p.resource_slots != '[]'::jsonb
          AND (elem ->> 'resource_type') NOT IN (SELECT slot_name FROM resource_slot_types)
        ON CONFLICT DO NOTHING
    """)
    )

    # From deployment_revisions.resource_slots
    conn.execute(
        sa.text("""
        INSERT INTO resource_slot_types (slot_name, slot_type, rank)
        SELECT DISTINCT kv.key, 'count', 0
        FROM deployment_revisions dr, jsonb_each_text(dr.resource_slots) AS kv(key, value)
        WHERE dr.resource_slots IS NOT NULL
          AND kv.key NOT IN (SELECT slot_name FROM resource_slot_types)
        ON CONFLICT DO NOTHING
    """)
    )

    # 5. Backfill model_card_resource_requirements
    conn.execute(
        sa.text("""
        INSERT INTO model_card_resource_requirements (model_card_id, slot_name, min_quantity)
        SELECT mc.id, kv.key, _tmp_parse_binary_size(kv.value)
        FROM model_cards mc, jsonb_each_text(mc.min_resource -> 'slots') AS kv(key, value)
        WHERE mc.min_resource IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    )

    # 6. Backfill preset_resource_slots
    conn.execute(
        sa.text("""
        INSERT INTO preset_resource_slots (preset_id, slot_name, quantity)
        SELECT p.id, elem ->> 'resource_type', _tmp_parse_binary_size(elem ->> 'quantity')
        FROM deployment_revision_presets p,
             jsonb_array_elements(p.resource_slots) AS elem
        WHERE p.resource_slots IS NOT NULL
          AND p.resource_slots != '[]'::jsonb
        ON CONFLICT DO NOTHING
    """)
    )

    # 7. Backfill deployment_revision_resource_slots
    conn.execute(
        sa.text("""
        INSERT INTO deployment_revision_resource_slots (revision_id, slot_name, quantity)
        SELECT dr.id, kv.key, _tmp_parse_binary_size(kv.value)
        FROM deployment_revisions dr, jsonb_each_text(dr.resource_slots) AS kv(key, value)
        WHERE dr.resource_slots IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    )

    # 8. Clean up the temporary helper function
    conn.execute(sa.text("DROP FUNCTION IF EXISTS _tmp_parse_binary_size(text)"))

    # 9. Drop JSONB columns
    op.drop_column("model_cards", "min_resource")
    op.drop_column("deployment_revision_presets", "resource_slots")
    op.drop_column("deployment_revisions", "resource_slots")


def downgrade() -> None:
    # Restore JSONB columns
    op.add_column(
        "deployment_revisions",
        sa.Column("resource_slots", pgsql.JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "deployment_revision_presets",
        sa.Column("resource_slots", pgsql.JSONB(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "model_cards",
        sa.Column("min_resource", pgsql.JSONB(), nullable=True),
    )

    # Restore data from normalized tables
    conn = op.get_bind()

    # Restore model_cards.min_resource
    conn.execute(
        sa.text("""
        UPDATE model_cards mc
        SET min_resource = sub.slots_json
        FROM (
            SELECT model_card_id,
                   jsonb_build_object('slots', jsonb_object_agg(slot_name, min_quantity::text))
                   AS slots_json
            FROM model_card_resource_requirements
            GROUP BY model_card_id
        ) sub
        WHERE mc.id = sub.model_card_id
    """)
    )

    # Restore deployment_revision_presets.resource_slots
    conn.execute(
        sa.text("""
        UPDATE deployment_revision_presets p
        SET resource_slots = sub.slots_json
        FROM (
            SELECT preset_id,
                   jsonb_agg(jsonb_build_object(
                       'resource_type', slot_name,
                       'quantity', quantity::text
                   )) AS slots_json
            FROM preset_resource_slots
            GROUP BY preset_id
        ) sub
        WHERE p.id = sub.preset_id
    """)
    )

    # Restore deployment_revisions.resource_slots
    conn.execute(
        sa.text("""
        UPDATE deployment_revisions dr
        SET resource_slots = sub.slots_json
        FROM (
            SELECT revision_id,
                   jsonb_object_agg(slot_name, quantity::text) AS slots_json
            FROM deployment_revision_resource_slots
            GROUP BY revision_id
        ) sub
        WHERE dr.id = sub.revision_id
    """)
    )

    # Drop normalized tables
    op.drop_table("deployment_revision_resource_slots")
    op.drop_table("preset_resource_slots")
    op.drop_table("model_card_resource_requirements")
