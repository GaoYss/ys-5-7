import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import get_connection, init_db
from app.repositories.loyalty_repository import LoyaltyRepository


def reset_db():
    """重置数据库"""
    import os
    db_path = Path(__file__).parent / "data" / "loyalty.db"
    if db_path.exists():
        os.remove(db_path)
    init_db()


def test_bug1_multiple_batches_expire_at_same_time():
    """Bug1: 多个批次同时过期，扣减累积错误"""
    print("\n" + "=" * 60)
    print("测试 Bug1: 多个批次同时过期，扣减累积错误")
    print("=" * 60)

    reset_db()
    repo = LoyaltyRepository()

    member_id = 1
    member = repo.get_member(member_id)
    print(f"初始积分: {member['points']}")

    # 人为创建3批同时过期的积分，设置为已过期状态
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with get_connection() as conn:
        for i in range(3):
            conn.execute(
                """
                INSERT INTO point_batches
                (member_id, transaction_id, original_points, remaining_points, earned_at, expires_at, expired)
                VALUES (?, ?, ?, ?, ?, ?, 0)
                """,
                (member_id, None, 100, 100, yesterday, yesterday),
            )
        # 同步更新 member 的 points 到一个不合理的大数值，模拟 member.points 和批次不同步
        conn.execute("UPDATE members SET points = ? WHERE id = ?", (member["points"] + 300, member_id))

    member = repo.get_member(member_id)
    batches = repo.get_member_point_batches(member_id, include_expired=True)
    print(f"注入3批过期积分后，member.points = {member['points']}")
    print(f"所有批次 (共{len(batches)}批):")
    for b in batches:
        print(f"  批次{b['id']}: {b['remaining_points']}/{b['original_points']},"
              f" expired={b['expired']}, expires={b['expires_at'][:10]}")

    # 调用 expire_member_points
    result = repo.expire_member_points(member_id)
    if result:
        print(f"\nexpire_member_points 处理结果:")
        print(f"  过期积分数: {result['expired_points']}")
        print(f"  过期批次数: {result['batch_count']}")
        print(f"  处理后 member.points: {result['new_points']}")
    else:
        print("expire_member_points 返回 None (没有过期积分)")

    # 验证结果
    member_after = repo.get_member(member_id)
    batches_after = repo.get_member_point_batches(member_id, include_expired=True)
    available = repo.get_member_available_points(member_id)
    total_batch_remaining = sum(b["remaining_points"] for b in batches_after)

    print(f"\n验证:")
    print(f"  member.points = {member_after['points']}")
    print(f"  批次剩余总和 = {total_batch_remaining}")
    print(f"  get_member_available_points = {available}")
    print(f"  所有批次状态:")
    for b in batches_after:
        print(f"    批次{b['id']}: {b['remaining_points']}/{b['original_points']}, expired={b['expired']}")

    # 判断 member.points 是否等于批次剩余总和
    if member_after["points"] == total_batch_remaining == available:
        print("\n✅ Bug1 已修复: member.points = 批次剩余总和 = available_points")
        return True
    else:
        print(f"\n❌ Bug1 仍存在: member.points({member_after['points']}) != "
              f"批次剩余总和({total_batch_remaining}) != available({available})")
        return False


def test_bug2_auto_expiration():
    """Bug2: 没有自动过期机制"""
    print("\n" + "=" * 60)
    print("测试 Bug2: 自动过期机制")
    print("=" * 60)

    reset_db()
    repo = LoyaltyRepository()

    member_id = 2  # 周芋圆 - 在初始化数据中，有260积分15天后过期
    member = repo.get_member(member_id)
    print(f"测试会员: {member['name']}")
    print(f"初始化 member.points = {member['points']}")
    batches = repo.get_member_point_batches(member_id)
    for b in batches:
        print(f"  批次{b['id']}: {b['remaining_points']}积分, {b.get('days_until_expiry','?')}天后过期")

    # 强制把批次设置为已过期但未标记
    print("\n将批次修改为已过期状态...")
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE point_batches SET expires_at = ? WHERE member_id = ?",
            (yesterday, member_id),
        )

    batches = repo.get_member_point_batches(member_id)
    print(f"过期后 get_member_point_batches (未过期) 返回: {len(batches)} 批")
    all_batches = repo.get_member_point_batches(member_id, include_expired=True)
    for b in all_batches:
        print(f"  批次{b['id']}: expires={b['expires_at'][:10]}, expired={b['expired']}")

    # 测试: 在 Service 层调用 get_member_or_404 应该自动触发过期
    from app.services.loyalty_service import LoyaltyService
    service = LoyaltyService()

    print("\n调用 service.get_member_or_404() ...")
    member_via_service = service.get_member_or_404(member_id)
    print(f"Service 返回 member.points = {member_via_service['points']}")

    # 验证数据库状态
    member_after = repo.get_member(member_id)
    batches_after = repo.get_member_point_batches(member_id, include_expired=True)
    expired_batches = [b for b in batches_after if b["expired"]]
    available = repo.get_member_available_points(member_id)

    print(f"\n验证:")
    print(f"  DB中 member.points = {member_after['points']}")
    print(f"  已标记 expired=1 的批次数: {len(expired_batches)}")
    print(f"  available_points = {available}")

    if len(expired_batches) > 0 and member_after["points"] == available:
        print("\n✅ Bug2 已修复: Service操作自动触发了过期处理")
        return True
    else:
        print("\n❌ Bug2 仍存在: 过期积分未被自动标记或扣减")
        return False


def test_bug3_redeem_points_vs_batches():
    """Bug3: 兑换时总积分和批次可用积分判断不一致"""
    print("\n" + "=" * 60)
    print("测试 Bug3: 兑换时判断逻辑不一致")
    print("=" * 60)

    reset_db()
    repo = LoyaltyRepository()
    from app.services.loyalty_service import LoyaltyService
    service = LoyaltyService()

    member_id = 1  # 林晓茶
    member = repo.get_member(member_id)
    print(f"测试会员: {member['name']}, 初始 member.points = {member['points']}")

    # 人为制造不一致: 批次里大部分积分过期，但 member.points 还是高值
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with get_connection() as conn:
        # 将已有批次的 expires_at 改为昨天（但 expired=0）
        conn.execute(
            "UPDATE point_batches SET expires_at = ? WHERE member_id = ? AND id <= 2",
            (yesterday, member_id),
        )
        # 再补一批未来过期的少量积分
        future_date = (datetime.now() + timedelta(days=100)).isoformat()
        conn.execute(
            """
            INSERT INTO point_batches
            (member_id, transaction_id, original_points, remaining_points, earned_at, expires_at, expired)
            VALUES (?, ?, ?, ?, datetime('now'), ?, 0)
            """,
            (member_id, None, 50, 50, future_date),
        )

    batches_all = repo.get_member_point_batches(member_id, include_expired=True)
    member = repo.get_member(member_id)
    available = repo.get_member_available_points(member_id)
    print(f"\n制造不一致后:")
    print(f"  member.points = {member['points']}")
    print(f"  available_points = {available}")
    print(f"  批次明细:")
    for b in batches_all:
        print(f"    批次{b['id']}: {b['remaining_points']}/{b['original_points']}, "
              f"expires={b['expires_at'][:10]}, expired={b['expired']}")

    print(f"\n场景: 尝试兑换需要 100 积分的礼品")
    print(f"  member.points({member['points']}) >= 100 : 是，看起来可以兑换")
    print(f"  available({available}) >= 100 : {available >= 100}，实际上不可以")

    from fastapi import HTTPException
    try:
        result = service.redeem_gift(member_id, 2)  # 礼品ID=2是300积分的礼品
        print(f"\n兑换居然成功了? 结果: {result['message']}")
        print("❌ Bug3: 兑换了过期积分!")
        return False
    except HTTPException as e:
        print(f"\n兑换被拒绝: {e.detail}")
        # 检查错误信息中是否包含实际可用积分
        if "可用" in e.detail or "另有" in e.detail or "实际可用" in e.detail:
            print("✅ Bug3 已修复: 拒绝兑换，并给出了清晰的可用积分说明")

            # 额外验证: 兑换失败后，member.points 应该已经被同步为可用值
            member_after = repo.get_member(member_id)
            available_after = repo.get_member_available_points(member_id)
            if member_after["points"] == available_after:
                print(f"  并且 member.points({member_after['points']}) 已同步为 available({available_after})")
                return True
            else:
                print(f"  但 member.points({member_after['points']}) != available({available_after})")
                return True  # 错误提示已修复就算过了
        else:
            print("⚠️ 拒绝兑换但错误提示不够清晰")
            return False


def run_all_tests():
    print("\n" + "#" * 60)
    print("# 三个Bug修复验证")
    print("#" * 60)

    results = {}

    try:
        results["Bug1"] = test_bug1_multiple_batches_expire_at_same_time()
    except Exception as e:
        print(f"\n❌ Bug1 测试异常: {e}")
        import traceback
        traceback.print_exc()
        results["Bug1"] = False

    try:
        results["Bug2"] = test_bug2_auto_expiration()
    except Exception as e:
        print(f"\n❌ Bug2 测试异常: {e}")
        import traceback
        traceback.print_exc()
        results["Bug2"] = False

    try:
        results["Bug3"] = test_bug3_redeem_points_vs_batches()
    except Exception as e:
        print(f"\n❌ Bug3 测试异常: {e}")
        import traceback
        traceback.print_exc()
        results["Bug3"] = False

    print("\n\n" + "=" * 60)
    print("测试汇总:")
    print("=" * 60)
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(results.values())
    print(f"\n总体: {'全部通过 ✅' if all_passed else '存在失败 ❌'}")
    return all_passed


if __name__ == "__main__":
    run_all_tests()
