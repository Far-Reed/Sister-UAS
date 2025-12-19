CREATE TABLE IF NOT EXISTS processed_events (
  id BIGSERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  event_id TEXT NOT NULL,
  source TEXT,
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ,
  payload JSONB,
  status TEXT NOT NULL DEFAULT 'received',
  UNIQUE (topic, event_id)
);

CREATE TABLE IF NOT EXISTS agg_stats (
  id INT PRIMARY KEY DEFAULT 1,
  received BIGINT DEFAULT 0,
  unique_processed BIGINT DEFAULT 0,
  duplicate_dropped BIGINT DEFAULT 0,
  uptime_start TIMESTAMPTZ DEFAULT now()
);

INSERT INTO agg_stats (id) VALUES (1) ON CONFLICT DO NOTHING;
