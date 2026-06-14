from fastapi import APIRouter

from app.schemas.loyalty import Tier
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("", response_model=list[Tier])
def list_tiers() -> list[dict]:
    return service.list_tiers()
