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
