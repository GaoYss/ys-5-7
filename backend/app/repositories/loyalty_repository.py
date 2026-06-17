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
                           CAST(julianday(date(expires_at)) - julianday(date('now')) AS INTEGER) AS days_until_expiry
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
                           CAST(julianday(date(expires_at)) - julianday(date('now')) AS INTEGER) AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    WHERE pb.member_id = ? AND pb.expired = 0 AND pb.remaining_points > 0
                      AND date(pb.expires_at) > date('now')
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
                           CAST(julianday(date(expires_at)) - julianday(date('now')) AS INTEGER) AS days_until_expiry
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
                           CAST(julianday(date(expires_at)) - julianday(date('now')) AS INTEGER) AS days_until_expiry
                    FROM point_batches pb
                    JOIN members m ON m.id = pb.member_id
                    WHERE pb.expired = 0 AND pb.remaining_points > 0
                      AND date(pb.expires_at) > date('now')
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
                WHERE member_id = ?
                  AND expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) > date('now')
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
                    MIN(CAST(julianday(date(pb.expires_at)) - julianday(date('now')) AS INTEGER)) AS days_until_expiry
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.expired = 0
                  AND pb.remaining_points > 0
                  AND date(pb.expires_at) > date('now')
                  AND date(pb.expires_at) <= date('now', '+' || ? || ' days')
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
                    MIN(CAST(julianday(date(pb.expires_at)) - julianday(date('now')) AS INTEGER)) AS days_until_expiry
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.member_id = ?
                  AND pb.expired = 0
                  AND pb.remaining_points > 0
                  AND date(pb.expires_at) > date('now')
                  AND date(pb.expires_at) <= date('now', '+' || ? || ' days')
                GROUP BY m.id, m.name
                """,
                (member_id, reminder_days),
            ).fetchone()
            reminder = row_to_dict(row)
            if reminder and reminder.get("days_until_expiry") is not None:
                reminder["days_until_expiry"] = int(reminder["days_until_expiry"])
            return reminder

    def expire_member_points(self, member_id: int) -> dict | None:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")

            rows = conn.execute(
                """
                SELECT pb.*, m.name AS member_name
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.member_id = ?
                  AND pb.expired = 0
                  AND pb.remaining_points > 0
                  AND date(pb.expires_at) <= date('now')
                ORDER BY pb.expires_at ASC
                """,
                (member_id,),
            ).fetchall()

            expired_batches = rows_to_dicts(rows)
            if not expired_batches:
                return None

            member_name = expired_batches[0]["member_name"]
            total_expired = sum(b["remaining_points"] for b in expired_batches)
            expired_points_list = [b["remaining_points"] for b in expired_batches]
            expired_dates = [b["expires_at"] for b in expired_batches]
            batch_ids = [b["id"] for b in expired_batches]

            for batch_id in batch_ids:
                conn.execute(
                    "UPDATE point_batches SET expired = 1, remaining_points = 0 WHERE id = ?",
                    (batch_id,),
                )

            row = conn.execute(
                """
                SELECT COALESCE(SUM(remaining_points), 0) AS active_total
                FROM point_batches
                WHERE member_id = ?
                  AND expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) > date('now')
                """,
                (member_id,),
            ).fetchone()
            new_points = row["active_total"]

            conn.execute(
                "UPDATE members SET points = ? WHERE id = ?",
                (new_points, member_id),
            )

            for expired_points, expired_date in zip(expired_points_list, expired_dates):
                conn.execute(
                    """
                    INSERT INTO point_transactions (member_id, type, points, note)
                    VALUES (?, 'expire', ?, ?)
                    """,
                    (
                        member_id,
                        -expired_points,
                        f"积分过期：{expired_points} 积分已于 {expired_date[:10]} 过期",
                    ),
                )

            return {
                "member_id": member_id,
                "member_name": member_name,
                "expired_points": total_expired,
                "batch_count": len(expired_batches),
                "new_points": new_points,
            }

    def expire_points(self) -> list[dict]:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")

            expired_rows = conn.execute(
                """
                SELECT pb.id AS batch_id, pb.member_id, pb.remaining_points,
                       pb.expires_at, m.name AS member_name
                FROM point_batches pb
                JOIN members m ON m.id = pb.member_id
                WHERE pb.expired = 0
                  AND pb.remaining_points > 0
                  AND date(pb.expires_at) <= date('now')
                ORDER BY pb.member_id, pb.expires_at ASC
                """
            ).fetchall()

            if not expired_rows:
                return []

            conn.execute(
                """
                UPDATE point_batches
                SET expired = 1, remaining_points = 0
                WHERE expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) <= date('now')
                """
            )

            member_expired = {}
            for row in expired_rows:
                mid = row["member_id"]
                if mid not in member_expired:
                    member_expired[mid] = {
                        "member_id": mid,
                        "member_name": row["member_name"],
                        "expired_points": 0,
                        "batch_count": 0,
                        "details": [],
                    }
                member_expired[mid]["expired_points"] += row["remaining_points"]
                member_expired[mid]["batch_count"] += 1
                member_expired[mid]["details"].append(
                    (row["remaining_points"], row["expires_at"])
                )

            active_rows = conn.execute(
                """
                SELECT member_id, COALESCE(SUM(remaining_points), 0) AS active_total
                FROM point_batches
                WHERE expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) > date('now')
                GROUP BY member_id
                """
            ).fetchall()
            active_map = {row["member_id"]: row["active_total"] for row in active_rows}

            for mid in member_expired:
                new_points = active_map.get(mid, 0)
                member_expired[mid]["new_points"] = new_points
                conn.execute(
                    "UPDATE members SET points = ? WHERE id = ?",
                    (new_points, mid),
                )

            for mid, info in member_expired.items():
                for expired_points, expired_date in info["details"]:
                    conn.execute(
                        """
                        INSERT INTO point_transactions (member_id, type, points, note)
                        VALUES (?, 'expire', ?, ?)
                        """,
                        (
                            mid,
                            -expired_points,
                            f"积分过期：{expired_points} 积分已于 {expired_date[:10]} 过期",
                        ),
                    )

            results = []
            for info in member_expired.values():
                results.append(
                    {
                        "member_id": info["member_id"],
                        "member_name": info["member_name"],
                        "expired_points": info["expired_points"],
                        "batch_count": info["batch_count"],
                        "new_points": info["new_points"],
                    }
                )
            return results

    def get_member_available_points(self, member_id: int) -> int:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(remaining_points), 0) AS available
                FROM point_batches
                WHERE member_id = ?
                  AND expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) > date('now')
                """,
                (member_id,),
            ).fetchone()
            return row["available"]

    def get_member_expired_unprocessed_points(self, member_id: int) -> int:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(remaining_points), 0) AS expired_unprocessed
                FROM point_batches
                WHERE member_id = ?
                  AND expired = 0
                  AND remaining_points > 0
                  AND date(expires_at) <= date('now')
                """,
                (member_id,),
            ).fetchone()
            return row["expired_unprocessed"]
