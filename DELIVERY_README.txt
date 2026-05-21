ORZEN VISION — PHASE 1 DELIVERY
==============================

Start here:

  docs/CLIENT_DELIVERY_PHASE1.md   What was delivered, acceptance, sign-off
  docs/CLIENT_DEMO_GUIDE.md        15-minute live demo script
  docs/API_REFERENCE_PHASE1.md     API contract for integrators

How to run (full guide):

  docs/HOW_TO_RUN.md

Quick start (developer):

  1. Copy .env.example to .env
  2. Run:  scripts\setup_local.ps1
  3. Run:  scripts\run_with_frontend.ps1
  4. Open: http://localhost:3000  (dashboard)
           http://127.0.0.1:8000/docs  (API)

Verify Phase 1:

  scripts\complete_phase1_handoff.ps1

Store edge (Jetson):

  docs/JETSON_DEPLOY.md

India cloud:

  docs/DEPLOY_INDIA.md

Phase 2+ roadmap:

  docs/ORZEN_BRIEF_ALIGNMENT.md

Do NOT commit .env or data/*.db to git.
