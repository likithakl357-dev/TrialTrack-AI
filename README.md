# TrialTrack AI — AIIA Hackathon PS 26046

Full-stack hackathon prototype: React + Vite, FastAPI, SQLAlchemy, SQLite locally / PostgreSQL with Docker. Uses synthetic demo data only.

## Local run (Windows)
Backend terminal:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
Frontend terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and API docs at http://localhost:8000/docs.

Demo users (all passwords `TrialTrack@123`): `admin@trialtrack.ai`, `pi@trialtrack.ai`, `pv@trialtrack.ai`, `ethics@trialtrack.ai`, `coordinator@trialtrack.ai`, `monitor@trialtrack.ai`, `regulator@trialtrack.ai`.

## Docker
From project root: `docker compose up --build`

## Innovation: TrialGuard
Transparent, rule-based 0–100 operational health score using recruitment progress, ethics approval, CTRI status, overdue milestones, open data queries, protocol deviations and open serious safety events. Each score displays reasons and suggested follow-up. This is operational decision support only, not a clinical prediction or safety causality tool.

## Included
Dashboard KPIs, study CRUD, recruitment tracking, ethics/CTRI milestone monitoring, AE/ADR/SAE capture, role-gated API actions, activity audit log, alerts, TrialGuard, FHIR ResearchStudy Bundle starter export, CDISC-oriented CSV starter export.

## Important limitation
This is NOT a validated or certified CTMS and does not establish GCP-ASU, ICMR, NDCT, CTRI, DPDP, ISO 27001 or CERT-In compliance. FHIR export is a starter, not profile-validated or connected to ABDM. CDISC CSV is not SDTM/ADaM/Define-XML submission-ready. Audit logs are application-level and not immutable against database administrators. E-signatures, validated MedDRA/WHODrug coding, production interoperability, security testing, privacy impact assessment, infrastructure residency, backup/DR, validation and institutional approval remain necessary before real clinical use. Use synthetic/de-identified data only.
