from fastapi import APIRouter

from backend_core.api.v1 import analytics, auth_routes, edge

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_routes.router)
api_v1.include_router(edge.router)
api_v1.include_router(analytics.router)
