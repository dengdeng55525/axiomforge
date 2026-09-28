-- Runtime schema is independent from schemas/knowledge_schema.sql (design validation fixture).
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS cf_sources (
 source_id TEXT PRIMARY KEY, source_key TEXT NOT NULL, content_sha256 TEXT NOT NULL,
 source_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cf_capability_versions (
 capability_id TEXT NOT NULL, version INTEGER NOT NULL, content_sha256 TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','extracted','verified','deprecated')),
 origin TEXT NOT NULL, card_json TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(capability_id,version), UNIQUE(capability_id,content_sha256)
);
CREATE TABLE IF NOT EXISTS cf_nodes (
 node_id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, properties_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cf_edges (
 edge_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES cf_nodes(node_id),
 target_id TEXT NOT NULL REFERENCES cf_nodes(node_id), relation TEXT NOT NULL,
 properties_json TEXT NOT NULL, UNIQUE(source_id,target_id,relation)
);
CREATE TABLE IF NOT EXISTS cf_runs (
 run_id TEXT PRIMARY KEY, status TEXT NOT NULL, report_json TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cf_run_revisions (
 run_id TEXT NOT NULL REFERENCES cf_runs(run_id), revision INTEGER NOT NULL,
 content_sha256 TEXT NOT NULL, report_json TEXT NOT NULL, created_at TEXT NOT NULL,
 PRIMARY KEY(run_id,revision), UNIQUE(run_id,content_sha256)
);
CREATE TABLE IF NOT EXISTS cf_events (
 event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES cf_runs(run_id),
 sequence INTEGER NOT NULL, event_type TEXT NOT NULL, event_json TEXT NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(run_id,sequence)
);
CREATE TABLE IF NOT EXISTS cf_artifacts (
 artifact_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES cf_runs(run_id),
 content_sha256 TEXT, artifact_json TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cf_failures (
 failure_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, run_id TEXT NOT NULL REFERENCES cf_runs(run_id),
 task_type TEXT NOT NULL, validated INTEGER NOT NULL CHECK(validated IN (0,1)),
 experience_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(run_id,fingerprint,validated)
);
CREATE INDEX IF NOT EXISTS cf_edges_from ON cf_edges(source_id,relation);
CREATE INDEX IF NOT EXISTS cf_edges_to ON cf_edges(target_id,relation);
CREATE INDEX IF NOT EXISTS cf_failures_scope ON cf_failures(task_type,validated);
CREATE INDEX IF NOT EXISTS cf_events_run ON cf_events(run_id,sequence);
CREATE INDEX IF NOT EXISTS cf_runs_updated ON cf_runs(updated_at DESC);
