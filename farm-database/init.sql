-- Farm Database (prototype schema).
-- Deliberately minimal: one table with the three fields the prototype needs.
-- Executed automatically by the official postgres image on first start.

CREATE TABLE IF NOT EXISTS sensor_readings (
    sensor_id   TEXT             NOT NULL,
    "timestamp" TIMESTAMPTZ      NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (sensor_id, "timestamp")
);

-- The composite primary key already gives us an index on (sensor_id, timestamp),
-- which PostgreSQL can scan backwards to answer "last reading of sensor X" quickly.
-- An index on timestamp alone speeds up the "latest readings of all sensors" view.
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
    ON sensor_readings ("timestamp" DESC);
