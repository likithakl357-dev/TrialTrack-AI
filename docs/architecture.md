# Architecture
React/Vite frontend → FastAPI REST API (JWT) → SQLAlchemy → SQLite locally or PostgreSQL in Docker. Modules: studies, recruitment, ethics/CTRI, safety events, TrialGuard rules engine, audit events and exports. FHIR export emits a starter ResearchStudy Bundle; CDISC export is a study-level CSV starter only. Neither is standards-validated.
