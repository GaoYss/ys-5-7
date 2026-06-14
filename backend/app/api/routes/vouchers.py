from fastapi import APIRouter

from app.schemas.loyalty import Voucher
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("", response_model=list[Voucher])
def list_vouchers() -> list[dict]:
    return service.list_vouchers()


@router.post("/birthday/issue", response_model=list[Voucher])
def issue_birthday_vouchers() -> list[dict]:
    return service.issue_birthday_vouchers()
