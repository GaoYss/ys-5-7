from fastapi import APIRouter

from app.schemas.loyalty import Gift, OperationResult, RedeemGiftRequest
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("", response_model=list[Gift])
def list_gifts() -> list[dict]:
    return service.list_gifts()


@router.post("/redeem", response_model=OperationResult)
def redeem_gift(payload: RedeemGiftRequest) -> dict:
    return service.redeem_gift(payload.member_id, payload.gift_id)
