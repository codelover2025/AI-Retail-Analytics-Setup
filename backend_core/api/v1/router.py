from fastapi import APIRouter

from backend_core.api.v1 import admin, analytics, auth_routes, edge, identity

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth_routes.router)
api_v1.include_router(admin.router)
api_v1.include_router(edge.router)
api_v1.include_router(analytics.router)
api_v1.include_router(identity.router)
