import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import init_db
from app.services.loyalty_service import LoyaltyService


def test_expiration_features():
    print("=" * 60)
    print("积分过期功能测试")
    print("=" * 60)

    init_db()
    service = LoyaltyService()

    print("\n1. 测试初始化数据")
    print("-" * 40)

    members = service.list_members()
    print(f"会员数量: {len(members)}")
    for m in members:
        expiring = m.get("expiring_soon_points", 0) or 0
        next_date = m.get("next_expiration_date", "")
        if next_date:
            next_date = next_date[:10]
        print(f"  - {m['name']}: {m['points']} 积分" + (f", 即将过期: {expiring} ({next_date})" if expiring else ""))

    rules = service.list_expiration_rules()
    print(f"\n过期规则数量: {len(rules)}")
    for r in rules:
        status = "✓ 启用" if r["active"] else "  未启用"
        print(f"  {status} - {r['name']}: 有效期{r['validity_days']}天, 提前{r['reminder_days']}天提醒")

    active_rule = service.get_active_expiration_rule()
    print(f"\n当前活跃规则: {active_rule['name']} (有效期{active_rule['validity_days']}天)")

    print("\n2. 测试积分批次查询")
    print("-" * 40)

    batches = service.list_point_batches(member_id=1)
    print(f"会员1的积分批次: {len(batches)} 批")
    for b in batches:
        status = "已过期" if b["expired"] else f"{b.get('days_until_expiry', '?')}天后过期"
        print(f"  - 批次{b['id']}: {b['remaining_points']}/{b['original_points']} 积分, {status}")

    print("\n3. 测试即将过期提醒")
    print("-" * 40)

    reminders = service.get_expiring_soon_members()
    print(f"即将过期提醒会员: {len(reminders)} 位")
    for r in reminders:
        print(f"  - {r['member_name']}: {r['expiring_points']}积分, {r['batch_count']}批, 最早{r['earliest_expiry_date'][:10]}到期 ({r['days_until_expiry']}天后)")

    print("\n4. 测试积分入账（创建新批次）")
    print("-" * 40)

    result = service.earn_points(member_id=1, amount=200, rule_id=1)
    print(f"入账结果: {result['message']}")
    print(f"会员新积分: {result['member']['points']}")

    batches_after = service.list_point_batches(member_id=1)
    print(f"入账后批次数量: {len(batches_after)}")
    latest_batch = batches_after[-1]
    print(f"最新批次: {latest_batch['remaining_points']}积分, 到期{latest_batch['expires_at'][:10]}")

    print("\n5. 测试礼品兑换（FIFO消耗）")
    print("-" * 40)

    member_before = service.get_member_or_404(1)
    print(f"兑换前积分: {member_before['points']}")

    batches_before = service.list_point_batches(member_id=1)
    print("兑换前各批次剩余:")
    for b in batches_before:
        if b["remaining_points"] > 0:
            print(f"  批次{b['id']}: {b['remaining_points']} 积分 (到期{b['expires_at'][:10]})")

    redeem_result = service.redeem_gift(member_id=1, gift_id=1)
    print(f"\n兑换结果: {redeem_result['message']}")
    print(f"消耗批次明细:")
    for cb in redeem_result.get("consumed_batches", []):
        print(f"  - 批次{cb['batch_id']}: 消耗{cb['consumed_points']}积分, 剩余{cb['remaining_after']}, 到期{cb['expires_at'][:10]}")

    batches_after = service.list_point_batches(member_id=1)
    print("\n兑换后各批次剩余:")
    for b in batches_after:
        status = "已用完" if b["remaining_points"] == 0 else str(b["remaining_points"])
        print(f"  批次{b['id']}: {status} 积分 (到期{b['expires_at'][:10]})")

    print("\n6. 测试创建新的过期规则")
    print("-" * 40)

    new_rule = service.create_expiration_rule(
        name="测试规则",
        description="测试有效期180天，提前15天提醒",
        validity_days=180,
        reminder_days=15
    )
    print(f"创建规则: {new_rule['name']} (ID: {new_rule['id']})")

    all_rules = service.list_expiration_rules()
    print(f"规则总数: {len(all_rules)}")

    activated = service.set_active_expiration_rule(new_rule["id"])
    print(f"已激活规则: {activated['name']} (active={activated['active']})")

    print("\n7. 测试仪表盘统计")
    print("-" * 40)

    dashboard = service.dashboard()
    print(f"会员数: {dashboard['members_count']}")
    print(f"总积分: {dashboard['total_points']}")
    print(f"即将过期会员: {dashboard.get('expiring_soon_members', 0)}")
    print(f"即将过期积分: {dashboard.get('expiring_soon_points', 0)}")

    print("\n8. 测试积分过期处理")
    print("-" * 40)
    expired = service.process_expired_points()
    print(f"已处理过期批次: {len(expired)}")
    for e in expired:
        print(f"  - {e['member_name']}: {e['expired_points']}积分过期")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    test_expiration_features()
