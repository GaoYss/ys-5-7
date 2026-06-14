from fastapi import APIRouter

from app.schemas.loyalty import EarnPointsRequest, OperationResult, PointRule, Transaction
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("/rules", response_model=list[PointRule])
def list_rules() -> list[dict]:
    return service.list_point_rules()


@router.post("/earn", response_model=OperationResult)
def earn_points(payload: EarnPointsRequest) -> dict:
    return service.earn_points(payload.member_id, payload.amount, payload.rule_id)


@router.get("/transactions", response_model=list[Transaction])
def list_transactions() -> list[dict]:
    return service.list_transactions()
