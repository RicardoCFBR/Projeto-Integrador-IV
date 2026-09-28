-- Reference DDL for PostgreSQL 16. Idempotent: safe to re-run.
-- Tables mirror the SQLAlchemy models in app/models.py.

CREATE TABLE IF NOT EXISTS device (
    id                          BIGSERIAL PRIMARY KEY,
    code                        VARCHAR(20)  NOT NULL,
    model                       VARCHAR(80),
    os_version                  VARCHAR(40),
    battery_design_capacity_mah INTEGER,
    is_active                   BOOLEAN      NOT NULL DEFAULT TRUE,
    enrolled_at                 TIMESTAMPTZ  NOT NULL DEFAULT now(),
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_device_code           UNIQUE (code),
    CONSTRAINT ck_device_capacity_positive CHECK (battery_design_capacity_mah > 0)
);

CREATE TABLE IF NOT EXISTS battery_telemetry (
    id                     BIGSERIAL PRIMARY KEY,
    device_id              BIGINT        NOT NULL REFERENCES device (id) ON DELETE CASCADE,
    recorded_at            TIMESTAMPTZ   NOT NULL,
    battery_level_pct      SMALLINT      NOT NULL,
    battery_temp_c         NUMERIC(5, 2) NOT NULL,
    voltage_mv             INTEGER       NOT NULL,
    is_charging            BOOLEAN       NOT NULL,
    cycle_count            INTEGER       NOT NULL,
    estimated_capacity_pct NUMERIC(5, 2),
    ram_available_mb       INTEGER,
    network_rx_mb          NUMERIC(12, 3),
    network_tx_mb          NUMERIC(12, 3),
    source                 VARCHAR(10)   NOT NULL DEFAULT 'synthetic',
    ingested_at            TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_battery_telemetry_device_instant   UNIQUE (device_id, recorded_at),
    CONSTRAINT ck_battery_telemetry_level_range      CHECK (battery_level_pct BETWEEN 0 AND 100),
    CONSTRAINT ck_battery_telemetry_voltage_positive CHECK (voltage_mv > 0),
    CONSTRAINT ck_battery_telemetry_cycles_non_negative CHECK (cycle_count >= 0),
    CONSTRAINT ck_battery_telemetry_capacity_range   CHECK (estimated_capacity_pct BETWEEN 0 AND 100),
    CONSTRAINT ck_battery_telemetry_ram_non_negative CHECK (ram_available_mb >= 0),
    CONSTRAINT ck_battery_telemetry_rx_non_negative  CHECK (network_rx_mb >= 0),
    CONSTRAINT ck_battery_telemetry_tx_non_negative  CHECK (network_tx_mb >= 0),
    CONSTRAINT ck_battery_telemetry_source_allowed   CHECK (source IN ('synthetic', 'real'))
);

CREATE INDEX IF NOT EXISTS ix_battery_telemetry_device_recorded_desc
    ON battery_telemetry (device_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS ml_model (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(80)  NOT NULL,
    version         VARCHAR(40)  NOT NULL,
    algorithm       VARCHAR(80)  NOT NULL,
    target          VARCHAR(40)  NOT NULL DEFAULT 'rul_cycles',
    trained_at      TIMESTAMPTZ  NOT NULL,
    training_rows   INTEGER,
    metrics         JSONB,
    hyperparameters JSONB,
    features        JSONB,
    artifact_path   VARCHAR(255),
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_model_name_version UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS risk_policy (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(80)   NOT NULL,
    high_below_cycles   NUMERIC(8, 2) NOT NULL,
    medium_below_cycles NUMERIC(8, 2) NOT NULL,
    source              VARCHAR(20)   NOT NULL DEFAULT 'experimental',
    is_active           BOOLEAN       NOT NULL DEFAULT FALSE,
    notes               TEXT,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT now(),
    CONSTRAINT uq_risk_policy_name            UNIQUE (name),
    CONSTRAINT ck_risk_policy_high_positive   CHECK (high_below_cycles > 0),
    CONSTRAINT ck_risk_policy_threshold_order CHECK (medium_below_cycles > high_below_cycles),
    CONSTRAINT ck_risk_policy_source_allowed  CHECK (source IN ('experimental', 'community', 'literature'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_risk_policy_single_active
    ON risk_policy (is_active) WHERE is_active;

CREATE TABLE IF NOT EXISTS battery_prediction (
    id              BIGSERIAL PRIMARY KEY,
    device_id       BIGINT        NOT NULL REFERENCES device (id) ON DELETE CASCADE,
    model_id        INTEGER       NOT NULL REFERENCES ml_model (id),
    risk_policy_id  INTEGER       REFERENCES risk_policy (id),
    predicted_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    telemetry_until TIMESTAMPTZ,
    rul_cycles      NUMERIC(8, 2) NOT NULL,
    risk_level      VARCHAR(10)   NOT NULL,
    features        JSONB,
    CONSTRAINT ck_battery_prediction_risk_level CHECK (risk_level IN ('low', 'medium', 'high'))
);

CREATE INDEX IF NOT EXISTS ix_battery_prediction_device_predicted_desc
    ON battery_prediction (device_id, predicted_at DESC);

-- Placeholder thresholds. Replace after the interview with the fleet operator.
INSERT INTO risk_policy (name, high_below_cycles, medium_below_cycles, source, is_active, notes)
VALUES ('experimental-v1', 50, 150, 'experimental', TRUE,
        'Placeholder thresholds for the proof of concept; not validated with the operator.')
ON CONFLICT (name) DO NOTHING;
