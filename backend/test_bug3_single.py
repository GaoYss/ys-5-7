import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import get_connection, init_db
from app.repositories.loyalty_repository import LoyaltyRepository
import os

db_path = Path(__file__).parent / "data" / "loyalty.db"
if db_path.exists():
    os.remove(db_path)
init_db()

repo = LoyaltyRepository()
from app.services.loyalty_service import LoyaltyService
service = LoyaltyService()

member_id = 1
member = repo.get_member(member_id)
print(f"初始: {member['name']}, points={member['points']}")

# 人为制造不一致: 批次里大部分积分过期，但 member.points 还是高值
yesterday = (datetime.now() - timedelta(days=1)).isoformat()
with get_connection() as conn:
    conn.execute(
        "UPDATE point_batches SET expires_at = ? WHERE member_id = ? AND id <= 2",
        (yesterday, member_id),
    )
    future_date = (datetime.now() + timedelta(days=100)).isoformat()
    conn.execute(
        """
        INSERT INTO point_batches
        (member_id, transaction_id, original_points, remaining_points, earned_at, expires_at, expired)
        VALUES (?, ?, ?, ?, datetime('now'), ?, 0)
        """,
        (member_id, None, 50, 50, future_date),
    )

member = repo.get_member(member_id)
available = repo.get_member_available_points(member_id)
print(f"制造不一致后: member.points={member['points']}, available={available}")

from fastapi import HTTPException

try:
    result = service.redeem_gift(member_id, 2)  # 需要300积分的礼品
    print(f"❌ 兑换居然成功了: {result['message']}")
except HTTPException as e:
    print(f"兑换被拒绝: {e.detail}")
    has_clear_message = any(word in e.detail for word in ["可用", "另有", "实际可用"])

    member_after = repo.get_member(member_id)
    available_after = repo.get_member_available_points(member_id)
    print(f"拒绝后: member.points={member_after['points']}, available={available_after}")

    batches_after = repo.get_member_point_batches(member_id, include_expired=True)
    for b in batches_after:
        print(f"  批次{b['id']}: expires={b['expires_at'][:10]}, expired={b['expired']}, remaining={b['remaining_points']}")

    if has_clear_message and member_after["points"] == available_after:
        print("\n✅ Bug3 PASS")
    else:
        print("\n❌ Bug3 FAIL")
