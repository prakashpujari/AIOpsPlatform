-- ─────────────────────────────────────────────
-- Initial Database Bootstrap
-- ─────────────────────────────────────────────

-- Create separate Keycloak database
CREATE DATABASE keycloak;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Schemas
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS aiops;

GRANT ALL PRIVILEGES ON DATABASE aiops_platform TO aiops;
GRANT ALL ON SCHEMA core TO aiops;
GRANT ALL ON SCHEMA audit TO aiops;
GRANT ALL ON SCHEMA aiops TO aiops;
