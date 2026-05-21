import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_core.api.routes import router as api_router
from backend_core.api.v1 import api_v1
from backend_core.api.websocket import router as ws_router
from shared.database.session import init_db

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Orzen Vision API",
    description="Phase 1: multi-tenant edge-cloud platform + analytics APIs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1)
app.include_router(api_router)
app.include_router(ws_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "phase": 1}


@app.get("/api/v1/health")
def health_v1():
    return {"status": "ok", "phase": 1}


def run() -> None:
    import uvicorn

    uvicorn.run("backend_core.main:app", host="0.0.0.0", port=8000, reload=False)
