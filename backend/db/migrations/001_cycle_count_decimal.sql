BEGIN;

ALTER TABLE battery_telemetry
ALTER COLUMN cycle_count TYPE NUMERIC(10, 2)
USING cycle_count::NUMERIC(10, 2);

COMMIT;