from fastapi import APIRouter

from app.schemas.loyalty import Dashboard, Member, MemberCreate, Transaction
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("", response_model=list[Member])
def list_members() -> list[dict]:
    return service.list_members()


@router.post("", response_model=Member)
def create_member(payload: MemberCreate) -> dict:
    return service.create_member(payload.name, payload.phone, payload.birthday)


@router.get("/dashboard", response_model=Dashboard)
def dashboard() -> dict:
    return service.dashboard()


@router.get("/{member_id}", response_model=Member)
def get_member(member_id: int) -> dict:
    return service.get_member_or_404(member_id)


@router.get("/{member_id}/transactions", response_model=list[Transaction])
def list_member_transactions(member_id: int) -> list[dict]:
    service.get_member_or_404(member_id)
    return service.list_transactions(member_id)
