from fastapi import APIRouter

from app.schemas.loyalty import ExpirationReminder, ExpirationRule, ExpirationRuleCreate
from app.services.loyalty_service import LoyaltyService

router = APIRouter()
service = LoyaltyService()


@router.get("/rules", response_model=list[ExpirationRule])
def list_expiration_rules() -> list[dict]:
    return service.list_expiration_rules()


@router.get("/rules/active", response_model=ExpirationRule)
def get_active_rule() -> dict:
    return service.get_active_expiration_rule()


@router.post("/rules", response_model=ExpirationRule)
def create_expiration_rule(payload: ExpirationRuleCreate) -> dict:
    return service.create_expiration_rule(
        payload.name, payload.description, payload.validity_days, payload.reminder_days
    )


@router.post("/rules/{rule_id}/activate", response_model=ExpirationRule)
def activate_expiration_rule(rule_id: int) -> dict:
    return service.set_active_expiration_rule(rule_id)


@router.get("/reminders", response_model=list[ExpirationReminder])
def get_expiring_soon_reminders() -> list[dict]:
    return service.get_expiring_soon_members()
