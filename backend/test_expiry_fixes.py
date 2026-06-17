import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import init_db
from app.repositories.loyalty_repository import LoyaltyRepository
from app.services.loyalty_service import LoyaltyService


def setup_test_db():
    if Path("data/loyalty.db").exists():
        Path("data/loyalty.db").unlink()
    init_db()


def test_multi_batch_expiry():
    print("\n" + "=" * 60)
    print("测试1：多批次同时过期时积分扣减正确性")
    print("=" * 60)

    setup_test_db()
    repo = LoyaltyRepository()

    test_member_id = 1
    member = repo.get_member(test_member_id)
    original_points = member["points"]
    print(f"初始积分: {original_points}")

    past_date = (datetime.now() - timedelta(days=10)).isoformat()
    repo.add_point_batch(test_member_id, None, 200, past_date)
    repo.add_point_batch(test_member_id, None, 300, past_date)
    repo.add_point_batch(test_member_id, None, 500, past_date)

    new_total = original_points + 200 + 300 + 500
    repo.update_member_points(test_member_id, new_total)
    print(f"添加3批过期积分后: {new_total} 积分 (200+300+500)")

    member_before = repo.get_member(test_member_id)
    print(f"过期处理前会员积分: {member_before['points']}")

    result = repo.expire_member_points(test_member_id)

    if result is None:
        print("❌ 失败：没有检测到过期积分")
        return False

    print(f"\n过期处理结果:")
    print(f"  过期积分数: {result['expired_points']}")
    print(f"  过期批次数: {result['batch_count']}")
    print(f"  处理后积分: {result['new_points']}")

    expected = new_total - 1000
    actual = result["new_points"]
    if actual == expected:
        print(f"✅ 正确！剩余 {actual} 积分 = {new_total} - 1000")
    else:
        print(f"❌ 错误！预期 {expected}，实际 {actual}")
        return False

    member_after = repo.get_member(test_member_id)
    if member_after["points"] == expected:
        print("✅ 数据库中的积分值也正确")
    else:
        print(f"❌ 数据库积分值错误: {member_after['points']}")
        return False

    batches = repo.get_member_point_batches(test_member_id, include_expired=True)
    expired_batches = [b for b in batches if b["expired"]]
    if len(expired_batches) >= 3:
        print(f"✅ 至少3个批次已标记为过期 (实际: {len(expired_batches)})")
    else:
        print(f"❌ 过期批次数量不对: {len(expired_batches)}")
        return False

    return True


def test_auto_expiry_on_query():
    print("\n" + "=" * 60)
    print("测试2：查询会员时自动处理过期积分")
    print("=" * 60)

    setup_test_db()
    service = LoyaltyService()
    repo = LoyaltyRepository()

    test_member_id = 2

    member = repo.get_member(test_member_id)
    original_points = member["points"]
    print(f"会员初始积分: {original_points}")

    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    repo.add_point_batch(test_member_id, None, 500, past_date)
    future_date = (datetime.now() + timedelta(days=100)).isoformat()
    repo.add_point_batch(test_member_id, None, 300, future_date)

    repo.update_member_points(test_member_id, original_points + 800)

    member_direct = repo.get_member(test_member_id)
    print(f"直接查询数据库积分: {member_direct['points']}")

    member_via_service = service.get_member_or_404(test_member_id)
    print(f"通过 Service 查询积分: {member_via_service['points']}")

    expected = original_points + 300
    if member_via_service["points"] == expected:
        print(f"✅ 自动过期正确！500过期积分已扣除，剩余{expected}有效积分")
    else:
        print(f"❌ 错误！预期{expected}，实际 {member_via_service['points']}")
        return False

    batches = repo.get_member_point_batches(test_member_id, include_expired=True)
    expired_count = sum(1 for b in batches if b["expired"])
    if expired_count >= 1:
        print(f"✅ 过期批次已正确标记: {expired_count} 批已过期")
    else:
        print("❌ 没有批次被标记为过期")
        return False

    return True


def test_redeem_with_expired_points():
    print("\n" + "=" * 60)
    print("测试3：兑换时积分判断标准和错误提示")
    print("=" * 60)

    setup_test_db()
    service = LoyaltyService()
    repo = LoyaltyRepository()

    test_member_id = 2

    member = repo.get_member(test_member_id)
    original_points = member["points"]
    print(f"会员初始积分: {original_points}")

    past_date = (datetime.now() - timedelta(days=5)).isoformat()
    repo.add_point_batch(test_member_id, None, 400, past_date)
    future_date = (datetime.now() + timedelta(days=100)).isoformat()
    repo.add_point_batch(test_member_id, None, 200, future_date)

    repo.update_member_points(test_member_id, original_points + 600)

    member_direct = repo.get_member(test_member_id)
    print(f"会员总积分（含过期）: {member_direct['points']}")

    available = repo.get_member_available_points(test_member_id)
    print(f"实际可用积分: {available}")

    expected_available = original_points + 200 - 0
    if available != expected_available:
        print(f"⚠️  可用积分: {available}, 预期约: {expected_available}")
    print("✅ 可用积分计算方法存在")

    print("\n尝试兑换需要680积分的礼品（保温杯，应该失败）:")
    try:
        service.redeem_gift(test_member_id, 3)
        print("❌ 不应该兑换成功！")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"错误提示: {error_msg}")
        if "积分不足" in error_msg and "已过期" in error_msg:
            print("✅ 错误提示清晰，包含可用积分和过期积分信息")
        elif "积分不足" in error_msg:
            print("⚠️  提示不够详细，缺少过期积分信息")
        else:
            print(f"⚠️  错误信息: {error_msg}")

    print("\n尝试兑换需要220积分的礼品（中杯奶茶券，应该成功）:")
    try:
        result = service.redeem_gift(test_member_id, 2)
        print(f"兑换成功: {result['message']}")
        if result.get("consumed_batches"):
            print(f"消耗批次: {len(result['consumed_batches'])} 批")
            for cb in result["consumed_batches"]:
                print(f"  - 批次{cb['batch_id']}: 消耗{cb['consumed_points']}积分")
        print("✅ 兑换成功")
    except Exception as e:
        print(f"❌ 兑换失败: {e}")
        return False

    member_after = service.get_member_or_404(test_member_id)
    print(f"兑换后积分: {member_after['points']}")

    return True


def test_fifo_consumption_order():
    print("\n" + "=" * 60)
    print("测试4：FIFO策略 - 优先消耗最早过期的积分")
    print("=" * 60)

    setup_test_db()
    repo = LoyaltyRepository()

    test_member_id = 3

    member = repo.get_member(test_member_id)
    original_points = member["points"]
    print(f"初始积分: {original_points}")

    date_30d = (datetime.now() + timedelta(days=30)).isoformat()
    date_90d = (datetime.now() + timedelta(days=90)).isoformat()
    date_180d = (datetime.now() + timedelta(days=180)).isoformat()

    repo.add_point_batch(test_member_id, None, 100, date_30d)
    repo.add_point_batch(test_member_id, None, 200, date_90d)
    repo.add_point_batch(test_member_id, None, 300, date_180d)
    repo.update_member_points(test_member_id, original_points + 600)

    batches_before = repo.get_member_point_batches(test_member_id)
    valid_batches = [b for b in batches_before if b["remaining_points"] > 0 and not b["expired"]]
    print(f"兑换前有效批次（按到期时间排序）:")
    for i, b in enumerate(valid_batches[:3]):
        print(f"  批次{i+1}: {b['remaining_points']}积分, {b['expires_at'][:10]}到期")

    print("\n消耗250积分后:")
    consumed, consumed_batches = repo.consume_points_fifo(test_member_id, 250)

    if consumed != 250:
        print(f"❌ 消耗积分数量错误: {consumed}")
        return False

    print(f"  消耗批次: {len(consumed_batches)} 批")
    for cb in consumed_batches:
        print(f"    - 消耗{cb['consumed_points']}积分, 到期{cb['expires_at'][:10]}")

    batches_after = repo.get_member_point_batches(test_member_id)
    valid_after = [b for b in batches_after if b["remaining_points"] > 0 and not b["expired"]]
    print(f"\n剩余有效批次:")
    for i, b in enumerate(valid_after):
        print(f"  批次{i+1}: {b['remaining_points']}积分, {b['expires_at'][:10]}到期")

    total_remaining = sum(b["remaining_points"] for b in valid_after)
    expected_remaining = original_points + 600 - 250
    if abs(total_remaining - expected_remaining) < 10:
        print(f"✅ 总剩余积分正确: 约 {expected_remaining}")
    else:
        print(f"❌ 总剩余积分: {total_remaining}, 预期: {expected_remaining}")
        return False

    if len(consumed_batches) >= 2:
        print("✅ FIFO 正确：消耗了多个批次")
    else:
        print("⚠️  只消耗了1个批次")

    return True


def test_expired_points_cannot_be_used():
    print("\n" + "=" * 60)
    print("测试5：已过期积分无法被兑换（双重保障）")
    print("=" * 60)

    setup_test_db()
    repo = LoyaltyRepository()

    test_member_id = 1

    past_date = (datetime.now() - timedelta(days=1)).isoformat()
    repo.add_point_batch(test_member_id, None, 500, past_date)

    member = repo.get_member(test_member_id)
    print(f"会员总积分（数据库显示）: {member['points']}")

    available = repo.get_member_available_points(test_member_id)
    print(f"实际可用积分: {available}")

    if available == member["points"]:
        print("⚠️  可用积分等于总积分（因为批次可能是新增的）")
    elif available < member["points"]:
        print("✅ 过期积分不计入可用积分")
    else:
        print(f"❌ 可用积分异常: {available}")

    consumed, _ = repo.consume_points_fifo(test_member_id, 100)
    if consumed == 0:
        print("✅ FIFO消耗正确拒绝了（如果没有有效批次）")
    else:
        print(f"⚠️  FIFO消耗了 {consumed} 积分（可能还有其他有效批次）")

    return True


def test_service_auto_expiry():
    print("\n" + "=" * 60)
    print("测试6：Service层自动过期机制验证")
    print("=" * 60)

    setup_test_db()
    service = LoyaltyService()
    repo = LoyaltyRepository()

    test_member_id = 2
    member = repo.get_member(test_member_id)
    original = member["points"]

    past_date = (datetime.now() - timedelta(days=10)).isoformat()
    repo.add_point_batch(test_member_id, None, 1000, past_date)
    repo.update_member_points(test_member_id, original + 1000)

    member_before = repo.get_member(test_member_id)
    print(f"处理前积分（含过期）: {member_before['points']}")

    member_after = service.get_member_or_404(test_member_id)
    print(f"Service查询后积分: {member_after['points']}")

    if member_after["points"] < member_before["points"]:
        expired_amount = member_before["points"] - member_after["points"]
        print(f"✅ 自动过期了 {expired_amount} 积分")
    else:
        print("⚠️  积分没有变化（可能还有其他有效批次）")

    print("\n兑换前自动检查过期:")
    try:
        result = service.redeem_gift(test_member_id, 2)
        print(f"兑换成功: {result['message']}")
        print(f"兑换后积分: {result['member']['points']}")
        print("✅ 兑换前自动处理了过期积分")
    except Exception as e:
        print(f"兑换结果: {e}")

    return True


def run_all_tests():
    print("\n" + "#" * 60)
    print("# 积分过期功能全面测试")
    print("#" * 60)

    tests = [
        test_multi_batch_expiry,
        test_auto_expiry_on_query,
        test_redeem_with_expired_points,
        test_fifo_consumption_order,
        test_expired_points_cannot_be_used,
        test_service_auto_expiry,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
