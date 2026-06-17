import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import get_connection, init_db
from app.repositories.loyalty_repository import LoyaltyRepository
from app.services.loyalty_service import LoyaltyService
import os


def reset_db():
    db_path = Path(__file__).parent / "data" / "loyalty.db"
    if db_path.exists():
        os.remove(db_path)
    init_db()


def test_redeem_error_structure():
    print("\n" + "=" * 60)
    print("测试1: 兑换失败错误响应 - 结构化字段")
    print("=" * 60)

    reset_db()
    service = LoyaltyService()

    member_id = 1
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

    from fastapi import HTTPException

    cases = [
        (1, 2, "points_insufficient_with_expired"),
        (1, 3, "points_insufficient"),
    ]

    all_pass = True

    for mid, gid, expected_error in cases:
        try:
            service.redeem_gift(mid, gid)
            print(f"  ❌ 兑换礼品{gid} 不应成功")
            all_pass = False
        except HTTPException as e:
            detail = e.detail
            is_dict = isinstance(detail, dict)
            has_fields = (
                is_dict
                and "error" in detail
                and "message" in detail
                and "available_points" in detail
                and "needed_points" in detail
                and "expired_points" in detail
            )
            error_match = detail.get("error") == expected_error if is_dict else False

            av = detail.get("available_points") if is_dict else None
            ne = detail.get("needed_points") if is_dict else None
            ex = detail.get("expired_points") if is_dict else None

            print(f"  兑换礼品{gid}: detail是dict={is_dict}, error={detail.get('error') if is_dict else 'N/A'}")
            print(f"    available={av}, needed={ne}, expired={ex}")

            if expected_error == "points_insufficient_with_expired":
                if av == 50 and ne is not None and ex > 0:
                    print(f"    ✅ 数值正确 (available=50, expired>0)")
                else:
                    print(f"    ❌ 数值异常")
                    all_pass = False

            if not has_fields:
                print(f"  ❌ 缺少字段")
                all_pass = False
            if not error_match:
                print(f"  ❌ error类型不匹配")
                all_pass = False

    if all_pass:
        print("\n✅ 测试1通过")
    else:
        print("\n❌ 测试1失败")
    return all_pass


def test_expire_and_reminder_sync():
    print("\n" + "=" * 60)
    print("测试2: 过期和即将过期提醒同步")
    print("=" * 60)

    reset_db()
    repo = LoyaltyRepository()
    service = LoyaltyService()

    member_id = 2
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO point_batches
            (member_id, transaction_id, original_points, remaining_points, earned_at, expires_at, expired)
            VALUES (?, ?, ?, ?, datetime('now'), ?, 0)
            """,
            (member_id, None, 300, 300, yesterday),
        )

    rule = repo.get_active_expiration_rule()
    reminders_before = repo.get_member_expiring_soon(
        member_id, rule["reminder_days"]
    )
    if reminders_before:
        print(f"  过期处理前的即将过期 (直接查询): {reminders_before.get('expiring_points')}积分")
    else:
        print("  过期处理前的即将过期 (直接查询): 无")

    members = service.list_members()
    member2 = next((m for m in members if m["id"] == member_id), None)

    reminders_after = repo.get_member_expiring_soon(
        member_id, rule["reminder_days"]
    )

    expiring_from_member = member2.get("expiring_soon_points") or 0 if member2 else 0
    expiring_from_reminder = reminders_after["expiring_points"] if reminders_after else 0

    print(f"\n  过期处理后会员2信息：")
    print(f"    points = {member2['points'] if member2 else 'N/A'}")
    print(f"    expiring_soon_points = {expiring_from_member} (来自list_members)")
    print(f"    expiring_soon_points = {expiring_from_reminder} (直接查询)")

    available = repo.get_member_available_points(member_id)
    print(f"    available_points = {available}")

    consistent = True
    if member2:
        if member2["points"] == available:
            print(f"  ✅ member.points == available: {member2['points']} == {available}")
        else:
            print(f"  ❌ member.points({member2['points']}) != available({available})")
            consistent = False
    else:
        print(f"  ❌ 找不到会员2")
        consistent = False

    if expiring_from_member == expiring_from_reminder:
        print(f"  ✅ 两个即将过期查询结果一致: {expiring_from_member}")
    else:
        print(f"  ❌ 两个即将过期查询结果不一致: {expiring_from_member} vs {expiring_from_reminder}")
        consistent = False

    if consistent:
        print("\n✅ 测试2通过")
        return True
    else:
        print("\n❌ 测试2失败")
        return False


def test_boundary_case():
    print("\n" + "=" * 60)
    print("测试3: 边界验证 - 刚好今天过期的批次")
    print("=" * 60)

    reset_db()
    repo = LoyaltyRepository()
    service = LoyaltyService()

    member_id = 1
    just_today = datetime.now().isoformat()

    with get_connection() as conn:
        conn.execute(
            "UPDATE point_batches SET expires_at = ? WHERE member_id = ? AND id = 1",
            (just_today, member_id),
        )

    members = service.list_members()
    member1 = next((m for m in members if m["id"] == member_id), None)
    rule = repo.get_active_expiration_rule()
    reminder = repo.get_member_expiring_soon(member_id, rule["reminder_days"])
    available = repo.get_member_available_points(member_id)

    print(f"  批次1 expires_at = {just_today[:10]} (今天)")
    print(f"  会员1 points = {member1['points'] if member1 else 'N/A'}")
    print(f"  会员1 available = {available}")
    print(f"  即将过期提醒: {reminder}")

    if member1 and member1["points"] == available:
        print(f"  ✅ 今天到期的批次已被正确处理: {member1['points']} == {available}")
        return True
    else:
        print(f"  ❌ 不一致")
        return False


def main():
    print("#" * 60)
    print("# 错误响应结构 & 过期提醒同步 测试")
    print("#" * 60)

    results = {}
    for name, fn in [
        ("错误响应结构", test_redeem_error_structure),
        ("过期提醒同步", test_expire_and_reminder_sync),
        ("边界日期处理", test_boundary_case),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"\n❌ {name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    print("\n" + "=" * 60)
    print("汇总:")
    all_pass = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print(f"\n总体: {'全部通过 ✅' if all_pass else '存在失败 ❌'}")
    return all_pass


if __name__ == "__main__":
    main()
