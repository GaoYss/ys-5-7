from app.db.database import get_connection
from app.repositories.base import row_to_dict, rows_to_dicts


class LoyaltyRepository:
    def list_members(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT m.*, t.name AS tier_name, t.discount_percent, t.birthday_bonus, t.benefits
                FROM members m
                JOIN tiers t ON t.id = m.tier_id
                ORDER BY m.id DESC
                """
            ).fetchall()
            return rows_to_dicts(rows)

    def get_member(self, member_id: int) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT m.*, t.name AS tier_name, t.discount_percent, t.birthday_bonus, t.benefits
                FROM members m
                JOIN tiers t ON t.id = m.tier_id
                WHERE m.id = ?
                """,
                (member_id,),
            ).fetchone()
            return row_to_dict(row)

    def create_member(self, name: str, phone: str, birthday: str, tier_id: int) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO members (name, phone, birthday, tier_id)
                VALUES (?, ?, ?, ?)
                """,
                (name, phone, birthday, tier_id),
            )
            member_id = cursor.lastrowid
        member = self.get_member(member_id)
        if member is None:
            raise RuntimeError("member creation failed")
        return member

    def update_member_points(self, member_id: int, points: int) -> None:
        with get_connection() as conn:
            conn.execute("UPDATE members SET points = ? WHERE id = ?", (points, member_id))

    def update_member_tier(self, member_id: int, tier_id: int) -> None:
        with get_connection() as conn:
            conn.execute("UPDATE members SET tier_id = ? WHERE id = ?", (tier_id, member_id))

    def list_tiers(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM tiers ORDER BY min_points").fetchall()
            return rows_to_dicts(rows)

    def best_tier_for_points(self, points: int) -> dict:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tiers WHERE min_points <= ? ORDER BY min_points DESC LIMIT 1",
                (points,),
            ).fetchone()
            if row is None:
                raise RuntimeError("no tier configured")
            return dict(row)

    def list_point_rules(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM point_rules ORDER BY id").fetchall()
            return rows_to_dicts(rows)

    def get_point_rule(self, rule_id: int) -> dict | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM point_rules WHERE id = ?", (rule_id,)).fetchone()
            return row_to_dict(row)

    def list_gifts(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM gifts ORDER BY points_cost").fetchall()
            return rows_to_dicts(rows)

    def get_gift(self, gift_id: int) -> dict | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM gifts WHERE id = ?", (gift_id,)).fetchone()
            return row_to_dict(row)

    def reduce_gift_stock(self, gift_id: int) -> None:
        with get_connection() as conn:
            conn.execute("UPDATE gifts SET stock = stock - 1 WHERE id = ? AND stock > 0", (gift_id,))

    def add_transaction(self, member_id: int, tx_type: str, points: int, note: str) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO point_transactions (member_id, type, points, note)
                VALUES (?, ?, ?, ?)
                """,
                (member_id, tx_type, points, note),
            )
            tx_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM point_transactions WHERE id = ?", (tx_id,)).fetchone()
            return dict(row)

    def list_transactions(self, member_id: int | None = None) -> list[dict]:
        with get_connection() as conn:
            if member_id is None:
                rows = conn.execute(
                    """
                    SELECT tx.*, m.name AS member_name
                    FROM point_transactions tx
                    JOIN members m ON m.id = tx.member_id
                    ORDER BY tx.id DESC
                    LIMIT 30
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT tx.*, m.name AS member_name
                    FROM point_transactions tx
                    JOIN members m ON m.id = tx.member_id
                    WHERE tx.member_id = ?
                    ORDER BY tx.id DESC
                    LIMIT 30
                    """,
                    (member_id,),
                ).fetchall()
            return rows_to_dicts(rows)

    def create_voucher(self, member_id: int, title: str, value: str, expires_at: str) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO vouchers (member_id, title, value, status, expires_at)
                VALUES (?, ?, ?, 'unused', ?)
                """,
                (member_id, title, value, expires_at),
            )
            voucher_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM vouchers WHERE id = ?", (voucher_id,)).fetchone()
            return dict(row)

    def birthday_voucher_exists(self, member_id: int, year: int) -> bool:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id FROM vouchers
                WHERE member_id = ?
                  AND title = '生日礼券'
                  AND substr(issued_at, 1, 4) = ?
                """,
                (member_id, str(year)),
            ).fetchone()
            return row is not None

    def list_vouchers(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT v.*, m.name AS member_name
                FROM vouchers v
                JOIN members m ON m.id = v.member_id
                ORDER BY v.id DESC
                LIMIT 50
                """
            ).fetchall()
            return rows_to_dicts(rows)

    def list_expiration_rules(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM point_expiration_rules ORDER BY id"
            ).fetchall()
            return rows_to_dicts(rows)

    def get_expiration_rule(self, rule_id: int) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM point_expiration_rules WHERE id = ?",
                (rule_id,),
            ).fetchone()
            return row_to_dict(row)

    def get_active_expiration_rule(self) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM point_expiration_rules WHERE active = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            return row_to_dict(row)

    def create_expiration_rule(
        self, name: str, description: str, validity_days: int, reminder_days: int
    ) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO point_expiration_rules (name, description, validity_days, reminder_days)
                VALUES (?, ?, ?, ?)
                """,
                (name, description, validity_days, reminder_days),
            )
            rule_id = cursor.lastrowid
            row = conn.execute(
                "SELECT * FROM point_expiration_rules WHERE id = ?", (rule_id,)
            ).fetchone()
            return row_to_dict(row)

    def update_expiration_rule_status(self, rule_id: int, active: bool) -> None:
        with get_connection() as conn:
            if active:
                conn.execute(
                    "UPDATE point_expiration_rules SET active = 0 WHERE active = 1"
                )
            conn.execute(
                "UPDATE point_expiration_rules SET active = ? WHERE id = ?",
                (1 if active else 0, rule_id),
            )

    def add_point_batch(
        self,
        member_id: int,
        transaction_id: int,
        points: int,
        expires_at: str,
    ) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO point_batches (member_id, transaction_id, original_points, remaining_points, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (member_id, transaction_id, points, points, expires_at),
            )
            batch_id = cursor.lastrowid
            row = conn.execute(
                "SELECT * FROM point_batches WHERE id = ?", (batch_id,)
            ).fetchone()
            return row_to_dict(row)

    def get_member_point_batches(
        self, member_id: int, include_expired: bool = False
    ) -> list[dict]:
        with get_connection() as conn:
            if include_expired:
                rows = conn.execute(
                    """
                    SELECT pb.*, m.name AS member_name,
                           julianday(expires_at) - julianday('now') AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    WHERE pb.member_id = ?
                    ORDER BY pb.expires_at ASC
                    """,
                    (member_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT pb.*, m.name AS member_name,
                           julianday(expires_at) - julianday('now') AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    WHERE pb.member_id = ? AND pb.expired = 0 AND pb.remaining_points > 0
                    ORDER BY pb.expires_at ASC
                    """,
                    (member_id,),
                ).fetchall()
            batches = rows_to_dicts(rows)
            for batch in batches:
                if batch.get("days_until_expiry") is not None:
                    batch["days_until_expiry"] = int(batch["days_until_expiry"])
                batch["expired"] = bool(batch["expired"])
            return batches

    def get_all_point_batches(
        self, include_expired: bool = False
    ) -> list[dict]:
        with get_connection() as conn:
            if include_expired:
                rows = conn.execute(
                    """
                    SELECT pb.*, m.name AS member_name,
                           julianday(expires_at) - julianday('now') AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    ORDER BY pb.expires_at ASC
                    LIMIT 100
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT pb.*, m.name AS member_name,
                           julianday(expires_at) - julianday('now') AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    WHERE pb.expired = 0 AND pb.remaining_points > 0
                    ORDER BY pb.expires_at ASC
                    LIMIT 100
                    """
                ).fetchall()
            batches = rows_to_dicts(rows)
            for batch in batches:
                if batch.get("days_until_expiry") is not None:
                    batch["days_until_expiry"] = int(batch["days_until_expiry"])
                batch["expired"] = bool(batch["expired"])
            return batches

    def consume_points_fifo(
        self, member_id: int, points_to_consume: int
    ) -> tuple[int, list[dict]]:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """
                SELECT * FROM point_batches
                WHERE member_id = ? AND expired = 0 AND remaining_points > 0
                ORDER BY expires_at ASC
                """,
                (member_id,),
            ).fetchall()

            batches = rows_to_dicts(rows)
            total_available = sum(b["remaining_points"] for b in batches)

            if total_available < points_to_consume:
                return 0, []

            remaining_needed = points_to_consume
            consumed_batches = []

            for batch in batches:
                if remaining_needed <= 0:
                    break

                consume_from_batch = min(batch["remaining_points"], remaining_needed)
                new_remaining = batch["remaining_points"] - consume_from_batch

                conn.execute(
                    "UPDATE point_batches SET remaining_points = ? WHERE id = ?",
                    (new_remaining, batch["id"]),
                )

                consumed_batches.append(
                    {
                        "batch_id": batch["id"],
                        "original_points": batch["original_points"],
                        "consumed_points": consume_from_batch,
                        "remaining_after": new_remaining,
                        "expires_at": batch["expires_at"],
                    }
                )

                remaining_needed -= consume_from_batch

            return points_to_consume - remaining_needed, consumed_batches

    def get_expiring_soon_members(self, reminder_days: int) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    m.id AS member_id,
                    m.name AS member_name,
                    SUM(pb.remaining_points) AS expiring_points,
                    COUNT(*) AS batch_count,
                    MIN(pb.expires_at) AS earliest_expiry_date,
                    MIN(julianday(pb.expires_at) - julianday('now')) AS days_until_expiry
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.expired = 0
                  AND pb.remaining_points > 0
                  AND julianday(pb.expires_at) - julianday('now') <= ?
                GROUP BY m.id, m.name
                ORDER BY days_until_expiry ASC
                """,
                (reminder_days,),
            ).fetchall()
            reminders = rows_to_dicts(rows)
            for reminder in reminders:
                if reminder.get("days_until_expiry") is not None:
                    reminder["days_until_expiry"] = int(
                        reminder["days_until_expiry"]
                    )
            return reminders

    def get_member_expiring_soon(
        self, member_id: int, reminder_days: int
    ) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    m.id AS member_id,
                    m.name AS member_name,
                    SUM(pb.remaining_points) AS expiring_points,
                    COUNT(*) AS batch_count,
                    MIN(pb.expires_at) AS earliest_expiry_date,
                    MIN(julianday(pb.expires_at) - julianday('now')) AS days_until_expiry
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.member_id = ?
                  AND pb.expired = 0
                  AND pb.remaining_points > 0
                  AND julianday(pb.expires_at) - julianday('now') <= ?
                GROUP BY m.id, m.name
                """,
                (member_id, reminder_days),
            ).fetchone()
            reminder = row_to_dict(row)
            if reminder and reminder.get("days_until_expiry") is not None:
                reminder["days_until_expiry"] = int(reminder["days_until_expiry"])
            return reminder

    def expire_points(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT pb.*, m.name AS member_name
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.expired = 0
                  AND pb.remaining_points > 0
                  AND julianday(pb.expires_at) - julianday('now') <= 0
                ORDER BY pb.expires_at ASC
                """
            ).fetchall()

            expired_batches = rows_to_dicts(rows)
            expired_details = []

            for batch in expired_batches:
                conn.execute(
                    "UPDATE point_batches SET expired = 1, remaining_points = 0 WHERE id = ?",
                    (batch["id"],),
                )

                member = self.get_member(batch["member_id"])
                if member:
                    new_points = max(0, member["points"] - batch["remaining_points"])
                    conn.execute(
                        "UPDATE members SET points = ? WHERE id = ?",
                        (new_points, batch["member_id"]),
                    )

                    self.add_transaction(
                        batch["member_id"],
                        "expire",
                        -batch["remaining_points"],
                        f"积分过期：{batch['remaining_points']} 积分已于 {batch['expires_at'][:10]} 过期",
                    )

                    expired_details.append(
                        {
                            "member_id": batch["member_id"],
                            "member_name": batch["member_name"],
                            "expired_points": batch["remaining_points"],
                            "expired_at": batch["expires_at"],
                        }
                    )

            return expired_details
