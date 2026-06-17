from datetime import date, datetime, timedelta

from fastapi import HTTPException, status

from app.repositories.loyalty_repository import LoyaltyRepository


class LoyaltyService:
    def __init__(self, repo: LoyaltyRepository | None = None) -> None:
        self.repo = repo or LoyaltyRepository()

    def _ensure_member_points_fresh(self, member_id: int) -> None:
        self.repo.expire_member_points(member_id)

    def _normalize_member(self, member: dict) -> dict:
        normalized = dict(member)
        benefits = normalized.get("benefits") or ""
        normalized["benefits"] = [item for item in benefits.split(";") if item]

        rule = self.repo.get_active_expiration_rule()
        if rule:
            reminder = self.repo.get_member_expiring_soon(
                normalized["id"], rule["reminder_days"]
            )
            if reminder:
                normalized["expiring_soon_points"] = reminder["expiring_points"]
                normalized["expiring_soon_count"] = reminder["batch_count"]
                normalized["next_expiration_date"] = reminder["earliest_expiry_date"]

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
        self.repo.expire_points()
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
        self._ensure_member_points_fresh(member_id)
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

        expiration_rule = self.repo.get_active_expiration_rule()
        if expiration_rule:
            expires_at = (datetime.now() + timedelta(days=expiration_rule["validity_days"])).isoformat()
            self.repo.add_point_batch(member_id, tx["id"], points, expires_at)

        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {"member": refreshed, "transaction": tx, "message": f"已增加 {points} 积分"}

    def list_gifts(self) -> list[dict]:
        return self.repo.list_gifts()

    def redeem_gift(self, member_id: int, gift_id: int) -> dict:
        expired_unprocessed = self.repo.get_member_expired_unprocessed_points(member_id)
        member = self.get_member_or_404(member_id)
        gift = self.repo.get_gift(gift_id)
        if gift is None or not gift["active"]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "gift_not_found",
                    "message": "礼品不存在或不可兑换",
                    "available_points": self.repo.get_member_available_points(member_id),
                    "needed_points": 0,
                    "expired_points": 0,
                },
            )
        if gift["stock"] <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "stock_empty",
                    "message": "礼品库存不足",
                    "available_points": self.repo.get_member_available_points(member_id),
                    "needed_points": gift["points_cost"],
                    "expired_points": 0,
                },
            )

        available_points = self.repo.get_member_available_points(member_id)

        if available_points < gift["points_cost"]:
            if expired_unprocessed > 0:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "points_insufficient_with_expired",
                        "message": f"可用积分不足。实际可用 {available_points} 积分，需 {gift['points_cost']} 积分（另有 {expired_unprocessed} 积分已过期）",
                        "available_points": available_points,
                        "needed_points": gift["points_cost"],
                        "expired_points": expired_unprocessed,
                    },
                )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "points_insufficient",
                    "message": f"积分不足。当前可用 {available_points} 积分，需 {gift['points_cost']} 积分",
                    "available_points": available_points,
                    "needed_points": gift["points_cost"],
                    "expired_points": 0,
                },
            )

        consumed, consumed_batches = self.repo.consume_points_fifo(
            member_id, gift["points_cost"]
        )
        if consumed == 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "consume_failed",
                    "message": "可用积分不足，部分积分可能已过期",
                    "available_points": self.repo.get_member_available_points(member_id),
                    "needed_points": gift["points_cost"],
                    "expired_points": 0,
                },
            )

        new_points = self.repo.get_member_available_points(member_id)
        self.repo.update_member_points(member_id, new_points)
        self.repo.reduce_gift_stock(gift_id)

        batch_summary = "；".join(
            [
                f"{b['consumed_points']}积分({b['expires_at'][:10]}到期)"
                for b in consumed_batches
            ]
        )
        tx = self.repo.add_transaction(
            member_id,
            "redeem",
            -gift["points_cost"],
            f"兑换礼品：{gift['name']}，消耗批次：{batch_summary}",
        )

        refreshed = self._refresh_member_tier({**member, "points": new_points})
        return {
            "member": refreshed,
            "transaction": tx,
            "message": f"已兑换 {gift['name']}",
            "consumed_batches": consumed_batches,
        }

    def issue_birthday_vouchers(self, today: date | None = None) -> list[dict]:
        today = today or date.today()
        self.repo.expire_points()
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
            tx = self.repo.add_transaction(member["id"], "birthday", tier["birthday_bonus"], "生日礼遇积分")

            expiration_rule = self.repo.get_active_expiration_rule()
            if expiration_rule:
                expires_at = (datetime.now() + timedelta(days=expiration_rule["validity_days"])).isoformat()
                self.repo.add_point_batch(member["id"], tx["id"], tier["birthday_bonus"], expires_at)

            issued.append(voucher)
        return issued

    def list_vouchers(self) -> list[dict]:
        return self.repo.list_vouchers()

    def list_transactions(self, member_id: int | None = None) -> list[dict]:
        return self.repo.list_transactions(member_id)

    def dashboard(self) -> dict:
        self.repo.expire_points()
        members = self.repo.list_members()
        gifts = self.repo.list_gifts()
        vouchers = self.repo.list_vouchers()

        rule = self.repo.get_active_expiration_rule()
        expiring_members = []
        if rule:
            expiring_members = self.repo.get_expiring_soon_members(rule["reminder_days"])

        return {
            "members_count": len(members),
            "total_points": sum(member["points"] for member in members),
            "gifts_count": len([gift for gift in gifts if gift["active"]]),
            "active_vouchers": len([voucher for voucher in vouchers if voucher["status"] == "unused"]),
            "expiring_soon_members": len(expiring_members),
            "expiring_soon_points": sum(m["expiring_points"] for m in expiring_members),
        }

    def list_expiration_rules(self) -> list[dict]:
        return self.repo.list_expiration_rules()

    def get_active_expiration_rule(self) -> dict:
        rule = self.repo.get_active_expiration_rule()
        if rule is None:
            raise HTTPException(status_code=404, detail="未找到启用的积分过期规则")
        return rule

    def create_expiration_rule(
        self, name: str, description: str, validity_days: int, reminder_days: int
    ) -> dict:
        if validity_days <= 0:
            raise HTTPException(status_code=400, detail="有效期必须大于0天")
        if reminder_days < 0 or reminder_days >= validity_days:
            raise HTTPException(status_code=400, detail="提醒天数必须在0到有效期之间")
        return self.repo.create_expiration_rule(name, description, validity_days, reminder_days)

    def set_active_expiration_rule(self, rule_id: int) -> dict:
        rule = self.repo.get_expiration_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="积分过期规则不存在")
        self.repo.update_expiration_rule_status(rule_id, True)
        updated_rule = self.repo.get_expiration_rule(rule_id)
        if updated_rule is None:
            raise HTTPException(status_code=404, detail="积分过期规则不存在")
        return updated_rule

    def list_point_batches(
        self, member_id: int | None = None, include_expired: bool = False
    ) -> list[dict]:
        if member_id is not None:
            self.get_member_or_404(member_id)
            return self.repo.get_member_point_batches(member_id, include_expired)
        return self.repo.get_all_point_batches(include_expired)

    def get_expiring_soon_members(self) -> list[dict]:
        rule = self.repo.get_active_expiration_rule()
        if rule is None:
            return []
        return self.repo.get_expiring_soon_members(rule["reminder_days"])

    def process_expired_points(self) -> list[dict]:
        return self.repo.expire_points()
