-- Executable initial design, not a claim that the Agent repository is implemented.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    uri TEXT NOT NULL,
    revision TEXT,
    content_sha256 TEXT NOT NULL CHECK(length(content_sha256) = 64),
    license TEXT NOT NULL,
    locator_json TEXT NOT NULL CHECK(json_valid(locator_json)),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK(kind IN ('TaskType','Capability','Algorithm','Transform','DatasetVersion','Metric','Environment','Source','Artifact','ValidationRun','FailureExperience')),
    label TEXT NOT NULL,
    properties_json TEXT NOT NULL CHECK(json_valid(properties_json))
);
CREATE TABLE IF NOT EXISTS edges (
    edge_id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL REFERENCES nodes(node_id),
    target_node_id TEXT NOT NULL REFERENCES nodes(node_id),
    relation TEXT NOT NULL CHECK(relation IN ('SOLVES','IMPLEMENTS','USES','REQUIRES','DERIVED_FROM','EVALUATED_ON','EVALUATES','MEASURED_BY','REPAIRS','SUPERSEDES','AVOIDED_BY')),
    source_id TEXT REFERENCES sources(source_id),
    properties_json TEXT NOT NULL CHECK(json_valid(properties_json)),
    UNIQUE(source_node_id, target_node_id, relation, source_id)
);
CREATE TABLE IF NOT EXISTS capability_versions (
    capability_id TEXT NOT NULL,
    version TEXT NOT NULL,
    node_id TEXT NOT NULL UNIQUE REFERENCES nodes(node_id),
    status TEXT NOT NULL CHECK(status IN ('draft','extracted','verified','deprecated')),
    content_json TEXT NOT NULL CHECK(json_valid(content_json)),
    created_at TEXT NOT NULL,
    PRIMARY KEY(capability_id, version)
);
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    source_sha256 TEXT NOT NULL CHECK(length(source_sha256) = 64),
    dependency_lock_sha256 TEXT NOT NULL,
    parent_artifact_id TEXT REFERENCES artifacts(artifact_id),
    relative_path TEXT NOT NULL,
    metadata_json TEXT NOT NULL CHECK(json_valid(metadata_json))
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    artifact_id TEXT REFERENCES artifacts(artifact_id),
    task_spec_json TEXT NOT NULL CHECK(json_valid(task_spec_json)),
    status TEXT NOT NULL CHECK(status IN ('queued','running','passed','failed','cancelled')),
    mode TEXT NOT NULL CHECK(mode IN ('real','mock','replay','manual_baseline')),
    report_json TEXT CHECK(report_json IS NULL OR json_valid(report_json)),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS failures (
    failure_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    status TEXT NOT NULL CHECK(status IN ('proposed','validated','rejected','deprecated')),
    scope_json TEXT NOT NULL CHECK(json_valid(scope_json)),
    experience_json TEXT NOT NULL CHECK(json_valid(experience_json))
);
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    created_at TEXT NOT NULL,
    UNIQUE(run_id, sequence)
);
CREATE INDEX IF NOT EXISTS edges_from ON edges(source_node_id, relation);
CREATE INDEX IF NOT EXISTS edges_to ON edges(target_node_id, relation);
CREATE INDEX IF NOT EXISTS failures_lookup ON failures(fingerprint, status);
