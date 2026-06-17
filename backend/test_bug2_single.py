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
member_id = 2

# 强制把批次设置为已过期但未标记
yesterday = (datetime.now() - timedelta(days=1)).isoformat()
with get_connection() as conn:
    conn.execute(
        "UPDATE point_batches SET expires_at = ? WHERE member_id = ?",
        (yesterday, member_id),
    )

from app.services.loyalty_service import LoyaltyService
service = LoyaltyService()

print("调用 get_member_or_404...")
member_via_service = service.get_member_or_404(member_id)
svc_points = member_via_service["points"]
print(f"Service返回 points={svc_points}")

member_after = repo.get_member(member_id)
available = repo.get_member_available_points(member_id)
print(f"DB points={member_after['points']}, available={available}")

batches_after = repo.get_member_point_batches(member_id, include_expired=True)
expired_batches = [b for b in batches_after if b["expired"]]
print(f"已过期批次数: {len(expired_batches)}")
for b in batches_after:
    print(f"  批次{b['id']}: expires={b['expires_at'][:10]}, expired={b['expired']}, remaining={b['remaining_points']}")

if len(expired_batches) > 0 and member_after["points"] == available == svc_points == 0:
    print("\n✅ Bug2 PASS")
else:
    print("\n❌ Bug2 FAIL")
