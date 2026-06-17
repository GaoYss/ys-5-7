import requests

BASE_URL = "http://localhost:8001/api"


def test_api():
    print("=" * 60)
    print("API 接口测试")
    print("=" * 60)

    print("\n1. 测试过期规则接口")
    print("-" * 40)

    resp = requests.get(f"{BASE_URL}/expiration/rules")
    print(f"GET /expiration/rules: {resp.status_code}")
    if resp.status_code == 200:
        rules = resp.json()
        print(f"  规则数量: {len(rules)}")
        for r in rules:
            status = "✓" if r["active"] else " "
            print(f"  {status} {r['name']}: {r['validity_days']}天有效期")

    resp = requests.get(f"{BASE_URL}/expiration/rules/active")
    print(f"\nGET /expiration/rules/active: {resp.status_code}")
    if resp.status_code == 200:
        rule = resp.json()
        print(f"  当前活跃规则: {rule['name']}")

    print("\n2. 测试即将过期提醒接口")
    print("-" * 40)

    resp = requests.get(f"{BASE_URL}/expiration/reminders")
    print(f"GET /expiration/reminders: {resp.status_code}")
    if resp.status_code == 200:
        reminders = resp.json()
        print(f"  即将过期会员: {len(reminders)} 位")
        for r in reminders:
            print(f"  - {r['member_name']}: {r['expiring_points']}积分, {r['days_until_expiry']}天后到期")

    print("\n3. 测试积分批次接口")
    print("-" * 40)

    resp = requests.get(f"{BASE_URL}/points/batches")
    print(f"GET /points/batches: {resp.status_code}")
    if resp.status_code == 200:
        batches = resp.json()
        print(f"  总批次数量: {len(batches)}")

    resp = requests.get(f"{BASE_URL}/points/batches/1")
    print(f"\nGET /points/batches/1: {resp.status_code}")
    if resp.status_code == 200:
        batches = resp.json()
        print(f"  会员1的批次: {len(batches)} 批")
        for b in batches[:3]:
            print(f"  - 批次{b['id']}: {b['remaining_points']}/{b['original_points']}积分, {b.get('days_until_expiry', '?')}天后过期")

    print("\n4. 测试会员接口（含过期信息）")
    print("-" * 40)

    resp = requests.get(f"{BASE_URL}/members")
    print(f"GET /members: {resp.status_code}")
    if resp.status_code == 200:
        members = resp.json()
        print(f"  会员数量: {len(members)}")
        for m in members:
            expiring = m.get("expiring_soon_points")
            if expiring:
                print(f"  - {m['name']}: {m['points']}积分, 即将过期{expiring}积分 ({m['next_expiration_date'][:10]})")
            else:
                print(f"  - {m['name']}: {m['points']}积分")

    print("\n5. 测试仪表盘接口")
    print("-" * 40)

    resp = requests.get(f"{BASE_URL}/members/dashboard")
    print(f"GET /members/dashboard: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  会员数: {data['members_count']}")
        print(f"  总积分: {data['total_points']}")
        print(f"  即将过期会员: {data.get('expiring_soon_members', 0)}")
        print(f"  即将过期积分: {data.get('expiring_soon_points', 0)}")

    print("\n6. 测试积分入账接口")
    print("-" * 40)

    earn_data = {"member_id": 1, "amount": 100, "rule_id": 1}
    resp = requests.post(f"{BASE_URL}/points/earn", json=earn_data)
    print(f"POST /points/earn: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"  {result['message']}")
        print(f"  会员新积分: {result['member']['points']}")

    print("\n7. 测试礼品兑换接口（FIFO）")
    print("-" * 40)

    redeem_data = {"member_id": 1, "gift_id": 1}
    resp = requests.post(f"{BASE_URL}/gifts/redeem", json=redeem_data)
    print(f"POST /gifts/redeem: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"  {result['message']}")
        if result.get("consumed_batches"):
            print(f"  消耗批次:")
            for cb in result["consumed_batches"]:
                print(f"    - 批次{cb['batch_id']}: 消耗{cb['consumed_points']}积分")

    print("\n8. 测试创建过期规则接口")
    print("-" * 40)

    rule_data = {
        "name": "API测试规则",
        "description": "通过API创建的测试规则",
        "validity_days": 90,
        "reminder_days": 10
    }
    resp = requests.post(f"{BASE_URL}/expiration/rules", json=rule_data)
    print(f"POST /expiration/rules: {resp.status_code}")
    if resp.status_code == 200:
        rule = resp.json()
        print(f"  创建成功: {rule['name']} (ID: {rule['id']})")

    print("\n9. 测试激活过期规则接口")
    print("-" * 40)

    resp = requests.post(f"{BASE_URL}/expiration/rules/3/activate")
    print(f"POST /expiration/rules/3/activate: {resp.status_code}")
    if resp.status_code == 200:
        rule = resp.json()
        print(f"  已激活: {rule['name']} (active={rule['active']})")

    print("\n10. 测试处理过期积分接口")
    print("-" * 40)

    resp = requests.post(f"{BASE_URL}/points/expire/process")
    print(f"POST /points/expire/process: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"  处理过期积分: {len(result)} 批")

    print("\n" + "=" * 60)
    print("✅ API 测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
