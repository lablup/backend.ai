"""
UUIDv7 generation on the database side.

The function is strictly increasing within a session, matching PostgreSQL 18's
built-in ``uuidv7()``. Once PG 18 is the minimum, the body becomes
``RETURN uuidv7();``.
"""

UUID_GENERATE_V7_DDL = """
CREATE OR REPLACE FUNCTION uuid_generate_v7() RETURNS uuid
LANGUAGE plpgsql VOLATILE PARALLEL UNSAFE AS $$
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
"""

DROP_UUID_GENERATE_V7_DDL = "DROP FUNCTION IF EXISTS uuid_generate_v7()"
