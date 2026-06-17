from fastapi import APIRouter, Query

from app.schemas.loyalty import EarnPointsRequest, OperationResult, PointBatch, PointRule, Transaction
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


@router.get("/batches", response_model=list[PointBatch])
def list_point_batches(
    member_id: int | None = Query(None, description="会员ID，不传则查询所有"),
    include_expired: bool = Query(False, description="是否包含已过期或已用完的批次"),
) -> list[dict]:
    return service.list_point_batches(member_id, include_expired)


@router.get("/batches/{member_id}", response_model=list[PointBatch])
def get_member_point_batches(
    member_id: int,
    include_expired: bool = Query(False, description="是否包含已过期或已用完的批次"),
) -> list[dict]:
    return service.list_point_batches(member_id, include_expired)


@router.post("/expire/process", response_model=list[dict])
def process_expired_points() -> list[dict]:
    return service.process_expired_points()
