CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS audit.batch_runs (
    batch_run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dag_run_id TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS audit.file_loads (
    file_load_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_run_id UUID REFERENCES audit.batch_runs(batch_run_id),
    file_name TEXT NOT NULL,
    target_table TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    error_message TEXT
);
