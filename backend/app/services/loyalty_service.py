from datetime import date, datetime, timedelta

from fastapi import HTTPException, status

from app.repositories.loyalty_repository import LoyaltyRepository


class LoyaltyService:
    def __init__(self, repo: LoyaltyRepository | None = None) -> None:
        self.repo = repo or LoyaltyRepository()

    def _normalize_member(self, member: dict) -> dict:
        normalized = dict(member)
        benefits = normalized.get("benefits") or ""
        normalized["benefits"] = [item for item in benefits.split(";") if item]
        return normalized

    def _normalize_tier(self, tier: dict) -> dict:
        normalized = dict(tier)
        normalized["benefits"] = [item for item in normalized["benefits"].split(";") if item]
        return normalized

    def _refresh_member_tier(self, member: dict) -> dict:
        tier = self.repo.best_tier_for_points(member["points"])
        if member["tier_id"] != tier["id"]:
            self.repo.update_member_tier(member["id"], tier["id"])
        refreshed = self.repo.get_member(member["id"])
        if refreshed is None:
            raise HTTPException(status_code=404, detail="会员不存在")
        return self._normalize_member(refreshed)

    def list_members(self) -> list[dict]:
        return [self._normalize_member(member) for member in self.repo.list_members()]

    def create_member(self, name: str, phone: str, birthday: str) -> dict:
        try:
            datetime.strptime(birthday, "%Y-%m-%d")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="生日格式必须为 YYYY-MM-DD") from exc

        tier = self.repo.best_tier_for_points(0)
        try:
            return self._normalize_member(self.repo.create_member(name, phone, birthday, tier["id"]))
        except Exception as exc:
            raise HTTPException(status_code=409, detail="手机号已存在或会员创建失败") from exc

    def get_member_or_404(self, member_id: int) -> dict:
        member = self.repo.get_member(member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="会员不存在")
        return self._normalize_member(member)

    def list_tiers(self) -> list[dict]:
        return [self._normalize_tier(tier) for tier in self.repo.list_tiers()]

    def list_point_rules(self) -> list[dict]:
        return self.repo.list_point_rules()

    def earn_points(self, member_id: int, amount: float, rule_id: int) -> dict:
        member = self.get_member_or_404(member_id)
        rule = self.repo.get_point_rule(rule_id)
        if rule is None or not rule["active"]:
            raise HTTPException(status_code=404, detail="积分规则不存在或未启用")

        points = int(amount / rule["amount_per_point"] * rule["multiplier"])
        if points <= 0:
            raise HTTPException(status_code=400, detail="本次消费未达到积分门槛")

        new_points = member["points"] + points
        self.repo.update_member_points(member_id, new_points)
        tx = self.repo.add_transaction(member_id, "earn", points, f"{rule['name']}：消费 {amount:.2f} 元")
        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {"member": refreshed, "transaction": tx, "message": f"已增加 {points} 积分"}

    def list_gifts(self) -> list[dict]:
        return self.repo.list_gifts()

    def redeem_gift(self, member_id: int, gift_id: int) -> dict:
        member = self.get_member_or_404(member_id)
        gift = self.repo.get_gift(gift_id)
        if gift is None or not gift["active"]:
            raise HTTPException(status_code=404, detail="礼品不存在或不可兑换")
        if gift["stock"] <= 0:
            raise HTTPException(status_code=400, detail="礼品库存不足")
        if member["points"] < gift["points_cost"]:
            raise HTTPException(status_code=400, detail="会员积分不足")

        new_points = member["points"] - gift["points_cost"]
        self.repo.update_member_points(member_id, new_points)
        self.repo.reduce_gift_stock(gift_id)
        tx = self.repo.add_transaction(member_id, "redeem", -gift["points_cost"], f"兑换礼品：{gift['name']}")
        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {"member": refreshed, "transaction": tx, "message": f"已兑换 {gift['name']}"}

    def issue_birthday_vouchers(self, today: date | None = None) -> list[dict]:
        today = today or date.today()
        issued = []
        for member in self.repo.list_members():
            birthday = datetime.strptime(member["birthday"], "%Y-%m-%d").date()
            if birthday.month != today.month or birthday.day != today.day:
                continue
            if self.repo.birthday_voucher_exists(member["id"], today.year):
                continue

            tier = self.repo.best_tier_for_points(member["points"])
            voucher = self.repo.create_voucher(
                member["id"],
                "生日礼券",
                f"{100 - tier['discount_percent']}折生日饮品券 + {tier['birthday_bonus']}积分"
                if tier["discount_percent"]
                else f"生日饮品券 + {tier['birthday_bonus']}积分",
                (today + timedelta(days=30)).isoformat(),
            )
            new_points = member["points"] + tier["birthday_bonus"]
            self.repo.update_member_points(member["id"], new_points)
            self.repo.add_transaction(member["id"], "birthday", tier["birthday_bonus"], "生日礼遇积分")
            issued.append(voucher)
        return issued

    def list_vouchers(self) -> list[dict]:
        return self.repo.list_vouchers()

    def list_transactions(self, member_id: int | None = None) -> list[dict]:
        return self.repo.list_transactions(member_id)

    def dashboard(self) -> dict:
        members = self.repo.list_members()
        gifts = self.repo.list_gifts()
        vouchers = self.repo.list_vouchers()
        return {
            "members_count": len(members),
            "total_points": sum(member["points"] for member in members),
            "gifts_count": len([gift for gift in gifts if gift["active"]]),
            "active_vouchers": len([voucher for voucher in vouchers if voucher["status"] == "unused"]),
        }
