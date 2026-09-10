-- Schema definition for the phishing prototype
-- This SQL file creates the tables used by the application when not using
-- Alembic. You can load it directly into a PostgreSQL database if you
-- prefer a manual setup or wish to inspect the schema.

CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    html_body TEXT NOT NULL,
    signals JSON,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE segments (
    id SERIAL PRIMARY KEY,
    age_bracket VARCHAR(50),
    gender VARCHAR(50),
    education VARCHAR(50)
);

CREATE TABLE targets (
    id SERIAL PRIMARY KEY,
    segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    recipient VARCHAR(255) NOT NULL,
    meta JSON
);

CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    channel VARCHAR(50) NOT NULL,
    launched_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',
    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    segment_id INTEGER NOT NULL REFERENCES segments(id) ON DELETE CASCADE
);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    target_id INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    meta JSON
);

-- Optional indexes to speed up lookups by foreign key and event type
CREATE INDEX idx_events_campaign ON events (campaign_id);
CREATE INDEX idx_events_target ON events (target_id);
CREATE INDEX idx_events_type ON events (event_type);