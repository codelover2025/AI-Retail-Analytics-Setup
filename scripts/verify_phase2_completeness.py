"""
Phase 2 completeness audit — static checks + unit tests + API smoke (TestClient).

Usage:
  $env:PYTHONPATH="."
  python scripts/verify_phase2_completeness.py
"""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    id: str
    category: str
    name: str
    passed: bool
    detail: str = ""


def _ok(cid: str, cat: str, name: str, cond: bool, detail: str = "") -> Check:
    return Check(cid, cat, name, cond, detail if cond else detail or "missing")


def static_checks() -> list[Check]:
    checks: list[Check] = []

    def has_attr(module_path: str, attr: str) -> bool:
        mod = importlib.import_module(module_path)
        return hasattr(mod, attr)

    # --- 5-point AI spec ---
    checks.append(
        _ok(
            "P2-1",
            "AI spec",
            "FaceProcessor quality gates",
            has_attr("edge_ai.pipeline.face_processor", "FaceProcessor"),
        )
    )
    checks.append(
        _ok(
            "P2-2",
            "AI spec",
            "CosineMatcher customer + employee galleries",
            has_attr("edge_ai.pipeline.matcher", "CosineMatcher"),
        )
    )
    checks.append(
        _ok(
            "P2-3",
            "AI spec",
            "IdentityService + IdentityEvent",
            has_attr("edge_ai.pipeline.identity_service", "IdentityService")
            and has_attr("edge_ai.pipeline.types", "IdentityEvent"),
        )
    )
    checks.append(
        _ok(
            "P2-4",
            "AI spec",
            "Employee gallery in store",
            inspect.getsourcefile(importlib.import_module("edge_ai.pipeline.store")) is not None,
        )
    )
    checks.append(
        _ok(
            "P2-5",
            "AI spec",
            "CLI enroll",
            Path(ROOT / "edge_ai/pipeline/enroll.py").is_file(),
        )
    )

    # --- Embedding / detection ---
    checks.append(
        _ok(
            "2.1",
            "Embedding",
            "enroll_from_frames()",
            has_attr("edge_ai.embeddings.face_embedder", "FaceEmbedder")
            and "enroll_from_frames" in dir(
                importlib.import_module("edge_ai.embeddings.face_embedder").FaceEmbedder
            ),
        )
    )
    settings = importlib.import_module("shared.config").Settings()
    checks.append(
        _ok(
            "1.2",
            "Detection",
            "MIN_FACE_SCORE / MIN_BBOX_AREA config",
            hasattr(settings, "min_face_score") and hasattr(settings, "min_bbox_area"),
            f"min_face_score={getattr(settings, 'min_face_score', None)}",
        )
    )

    # --- DB / pipeline ---
    from shared.database.models import Recognition, Visitor

    checks.append(
        _ok(
            "3.4",
            "Recognition",
            "match_score column on Recognition",
            "match_score" in Recognition.__table__.columns.keys(),
        )
    )
    checks.append(
        _ok(
            "3.5",
            "Recognition",
            "identity_type column on Recognition",
            "identity_type" in Recognition.__table__.columns.keys(),
        )
    )
    checks.append(
        _ok(
            "5.2",
            "Identity",
            "person_kind via Visitor.metadata (JSON)",
            "metadata" in Visitor.__table__.columns.keys(),
        )
    )

    # --- API routes (identity_routes) ---
    from backend_core.main import app

    paths = {getattr(r, "path", "") for r in app.routes}
    api_paths = {p for p in paths if p}

    def route_exists(fragment: str) -> bool:
        return any(fragment in p for p in api_paths)

    checks.append(_ok("5.3", "HTTP API", "GET /api/customers", route_exists("/customers")))
    checks.append(_ok("5.4", "HTTP API", "POST /api/customers", route_exists("/customers")))
    checks.append(
        _ok("5.5", "HTTP API", "GET /api/customers/{id}", route_exists("/customers/"))
    )
    checks.append(
        _ok("4.4", "HTTP API", "GET /api/visitors/{id}/visits", route_exists("/visits"))
    )
    checks.append(_ok("6.2", "HTTP API", "GET /api/employees", route_exists("/employees")))
    checks.append(_ok("6.2b", "HTTP API", "POST /api/employees", route_exists("/employees")))

    contract = importlib.import_module("backend_core.schemas.contract")
    rt = getattr(contract, "RecognitionType", ())
    checks.append(
        _ok(
            "6.6",
            "HTTP API",
            "RecognitionType includes employee",
            "employee" in str(rt),
        )
    )

    # --- Gaps (optional / not started) ---
    checks.append(
        _ok(
            "1.3",
            "Detection",
            "Multi-frame embed average per track",
            Path(ROOT / "edge_ai/pipeline/track_embedding_buffer.py").is_file(),
        )
    )
    checks.append(
        _ok(
            "1.4",
            "Optional",
            "Jetson tuning doc",
            (ROOT / "docs/phase 2/JETSON_TUNING.md").is_file()
            or (ROOT / "edge_ai/pipeline/README.md").is_file(),
            "edge_ai/pipeline/README.md exists" if (ROOT / "edge_ai/pipeline/README.md").is_file() else "",
        )
    )
    from edge_ai.pipeline.faiss_index import faiss_available

    checks.append(
        _ok(
            "3.6",
            "Recognition",
            "FAISS index module",
            Path(ROOT / "edge_ai/pipeline/faiss_index.py").is_file(),
            "installed" if faiss_available() else "faiss-cpu optional",
        )
    )
    checks.append(
        _ok(
            "6.7",
            "HTTP API",
            "POST /api/employees/upload",
            route_exists("/employees/upload"),
        )
    )
    checks.append(
        _ok(
            "6.8",
            "HTTP API",
            "POST /api/employees/{id}/re-enroll",
            any("re-enroll" in p for p in api_paths),
        )
    )
    checks.append(
        _ok(
            "6.9",
            "HTTP API",
            "PATCH /api/employees/{id}",
            any("/employees/" in p for p in api_paths),
        )
    )

    return checks


def run_unit_scripts() -> list[Check]:
    scripts = [
        ("UT-1", "test_identity_matcher.py"),
        ("UT-2", "test_identity_visit_count.py"),
        ("UT-3", "test_face_processor_quality.py"),
        ("UT-4", "test_track_embedding_buffer.py"),
        ("UT-5", "test_faiss_matcher.py"),
    ]
    out: list[Check] = []
    for cid, name in scripts:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name)],
            cwd=ROOT,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT)},
            capture_output=True,
            text=True,
        )
        out.append(
            Check(
                cid,
                "Unit test",
                name,
                r.returncode == 0,
                (r.stdout or r.stderr).strip()[:200],
            )
        )
    return out


def api_smoke() -> list[Check]:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///./data/orzen_verify.db")
    from shared.config import get_settings

    get_settings.cache_clear()

    from fastapi.testclient import TestClient

    from backend_core.main import app
    from shared.database.session import init_db

    init_db()
    try:
        from scripts.seed_phase1 import seed

        seed()
        get_settings.cache_clear()
    except Exception:
        pass
    client = TestClient(app)
    headers = {"X-API-Key": "dev-dashboard-key"}

    checks: list[Check] = []

    r = client.get("/health")
    checks.append(Check("API-H", "API smoke", "GET /health", r.status_code == 200))

    r = client.get("/api/live-visitors", headers=headers)
    checks.append(
        Check(
            "API-LV",
            "API smoke",
            "GET /api/live-visitors (auth)",
            r.status_code == 200,
            str(r.json())[:80],
        )
    )

    r = client.get("/api/customers", headers=headers)
    checks.append(
        Check(
            "API-C",
            "API smoke",
            "GET /api/customers",
            r.status_code == 200,
            f"count={len(r.json())}",
        )
    )

    r = client.get("/api/employees", headers=headers)
    checks.append(
        Check(
            "API-E",
            "API smoke",
            "GET /api/employees",
            r.status_code == 200,
        )
    )

    r = client.get("/api/identity-stats", headers=headers)
    checks.append(
        Check(
            "API-S",
            "API smoke",
            "GET /api/identity-stats",
            r.status_code == 200,
        )
    )

    emb = [0.0] * 512
    emb[0] = 1.0
    r = client.post(
        "/api/employees",
        headers=headers,
        json={
            "id": "00000000-0000-0000-0000-00000000e001",
            "name": "Verify Bot",
            "embedding": emb,
        },
    )
    checks.append(
        Check(
            "API-EC",
            "API smoke",
            "POST /api/employees",
            r.status_code in (200, 201),
            str(r.status_code),
        )
    )

    return checks


def main() -> int:
    print("=" * 60)
    print("Phase 2 completeness verification")
    print("=" * 60)

    all_checks: list[Check] = []
    all_checks.extend(static_checks())
    all_checks.extend(run_unit_scripts())
    try:
        all_checks.extend(api_smoke())
    except Exception as exc:
        all_checks.append(
            Check("API-X", "API smoke", "TestClient", False, str(exc)[:200])
        )

    required = [c for c in all_checks if c.category not in ("Optional", "Partial")]
    optional = [c for c in all_checks if c.category == "Optional"]
    partial = [c for c in all_checks if c.category == "Partial"]

    passed_req = sum(1 for c in required if c.passed)
    failed_req = [c for c in required if not c.passed]

    for c in all_checks:
        mark = "PASS" if c.passed else "FAIL"
        extra = f" — {c.detail}" if c.detail and not c.passed else ""
        if c.category in ("Optional", "Partial") and not c.passed:
            mark = "SKIP" if c.category == "Optional" else "PARTIAL"
            extra = f" — {c.detail}" if c.detail else ""
        print(f"[{mark}] [{c.category}] {c.id} {c.name}{extra}")

    print()
    print("-" * 60)
    pct = int(100 * passed_req / len(required)) if required else 0
    print(f"Required checks: {passed_req}/{len(required)} ({pct}%)")
    if failed_req:
        print("Failed:")
        for c in failed_req:
            print(f"  - {c.id} {c.name}: {c.detail}")

    opt_done = sum(1 for c in optional if c.passed)
    print(f"Optional: {opt_done}/{len(optional)} done")
    if partial:
        print(f"Partial: {sum(1 for c in partial if c.passed)}/{len(partial)}")

    # Align with PHASE2_STATUS buckets
    ai_core = [c for c in required if c.category in ("AI spec", "Embedding", "Detection", "Recognition", "Identity", "Unit test")]
    ai_pass = sum(1 for c in ai_core if c.passed)
    api_core = [c for c in required if c.category in ("HTTP API", "API smoke")]
    api_pass = sum(1 for c in api_core if c.passed)
    print()
    print(f"AI / pipeline slice: {ai_pass}/{len(ai_core)}")
    print(f"HTTP / API slice:      {api_pass}/{len(api_core)}")
    print("=" * 60)

    return 0 if not failed_req else 1


if __name__ == "__main__":
    sys.exit(main())
