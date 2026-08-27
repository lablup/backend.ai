"""Initial rows for the ``resource_slot_types`` registry.

Mirrors the seed carried by migration ``ccf8ae5c90fe`` so that a database
built by ``mgr dbschema oneshot`` — which runs ``metadata.create_all()``
instead of the migrations — starts with the same registry.
"""

from __future__ import annotations

from sqlalchemy.engine import Connection

__all__ = ("seed_resource_slot_types",)

_SEED_SQL = """
    INSERT INTO resource_slot_types
        (slot_name, slot_type, display_name, description,
         display_unit, display_icon, number_format, rank)
    VALUES
        ('cpu',        'count', 'CPU',        'CPU',
         'Core',    'cpu',     '{"binary":false,"round_length":0}', 100),
        ('mem',        'bytes', 'RAM',        'Memory',
         'GiB',     'ram',     '{"binary":true,"round_length":0}',  200),
        ('cuda.device','count', 'GPU',        'CUDA-capable GPU',
         'GPU',     'nvidia',  '{"binary":false,"round_length":0}', 300),
        ('cuda.shares','count', 'fGPU',       'CUDA-capable GPU (fractional)',
         'fGPU',    'nvidia',  '{"binary":false,"round_length":2}', 400),
        ('rocm.device','count', 'GPU',        'ROCm-capable GPU',
         'GPU',     'rocm',    '{"binary":false,"round_length":0}', 500),
        ('tpu.device', 'count', 'TPU',        'TPU device',
         'GPU',     'tpu',     '{"binary":false,"round_length":0}', 600),
        ('ipu.device', 'count', 'IPU',        'IPU device',
         'IPU',     'ipu',     '{"binary":false,"round_length":0}', 700),
        ('atom.device','count', 'ATOM Device','ATOM',
         'ATOM',    'rebel',   '{"binary":false,"round_length":0}', 800),
        ('atom-plus.device','count','ATOM+ Device','ATOM+',
         'ATOM+',   'rebel',   '{"binary":false,"round_length":0}', 900),
        ('atom-max.device','count','ATOM Max Device','ATOM Max',
         'ATOM Max','rebel',   '{"binary":false,"round_length":0}', 1000),
        ('gaudi2.device','count','Gaudi 2 Device','Gaudi 2',
         'Gaudi 2', 'gaudi',   '{"binary":false,"round_length":0}', 1100),
        ('warboy.device','count','Warboy Device','Furiosa Warboy',
         'Warboy',  'furiosa', '{"binary":false,"round_length":0}', 1200),
        ('rngd.device','count', 'RNGD Device','Furiosa RNGD',
         'RNGD',    'furiosa', '{"binary":false,"round_length":0}', 1300),
        ('hyperaccel-lpu.device','count','Hyperaccel LPU Device','Hyperaccel LPU',
         'LPU',     'lpu',     '{"binary":false,"round_length":0}', 1400)
    ON CONFLICT (slot_name) DO NOTHING
"""


def seed_resource_slot_types(connection: Connection) -> None:
    connection.exec_driver_sql(_SEED_SQL)
