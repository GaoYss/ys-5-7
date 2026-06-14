from fastapi import APIRouter

from app.api.routes import gifts, members, points, tiers, vouchers

api_router = APIRouter()
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(points.router, prefix="/points", tags=["points"])
api_router.include_router(gifts.router, prefix="/gifts", tags=["gifts"])
api_router.include_router(tiers.router, prefix="/tiers", tags=["tiers"])
api_router.include_router(vouchers.router, prefix="/vouchers", tags=["vouchers"])
