import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.core.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    min_points INTEGER NOT NULL,
    discount_percent INTEGER NOT NULL,
    birthday_bonus INTEGER NOT NULL,
    benefits TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS point_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_per_point REAL NOT NULL,
    multiplier REAL NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    birthday TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    tier_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tier_id) REFERENCES tiers(id)
);

CREATE TABLE IF NOT EXISTS gifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    points_cost INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    description TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    points INTEGER NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id)
);

CREATE TABLE IF NOT EXISTS vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    value TEXT NOT NULL,
    status TEXT NOT NULL,
    issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT NOT NULL,
    FOREIGN KEY (member_id) REFERENCES members(id)
);
"""


SEED_SQL = """
INSERT OR IGNORE INTO tiers (id, name, min_points, discount_percent, birthday_bonus, benefits)
VALUES
    (1, '青铜会员', 0, 0, 20, '积分抵礼品;生日专属券'),
    (2, '白银会员', 300, 5, 50, '95折饮品;生日加赠50积分;新品试饮'),
    (3, '黄金会员', 800, 10, 100, '9折饮品;生日加赠100积分;新品优先兑换'),
    (4, '黑金会员', 1600, 15, 200, '85折饮品;生日加赠200积分;每月专属礼');

INSERT OR IGNORE INTO point_rules (id, name, description, amount_per_point, multiplier, active)
VALUES
    (1, '基础消费积分', '每消费10元获得1积分，活动期间可叠加倍率。', 10, 1, 1),
    (2, '周三双倍积分', '周三门店消费积分翻倍。', 10, 2, 1),
    (3, '新品推广三倍积分', '购买指定新品时享受三倍积分。', 10, 3, 1);

INSERT OR IGNORE INTO gifts (id, name, points_cost, stock, description, active)
VALUES
    (1, '珍珠加料券', 80, 120, '任意中大杯饮品可兑换一份珍珠。', 1),
    (2, '中杯奶茶券', 220, 45, '可兑换指定中杯经典奶茶一杯。', 1),
    (3, '保温杯', 680, 15, '门店联名随行保温杯。', 1),
    (4, '生日蛋糕券', 520, 20, '可兑换一份迷你生日蛋糕。', 1);

INSERT OR IGNORE INTO members (id, name, phone, birthday, points, tier_id)
VALUES
    (1, '林晓茶', '13800000001', '1998-06-14', 860, 3),
    (2, '周芋圆', '13800000002', '1996-11-22', 260, 1),
    (3, '陈波波', '13800000003', '1994-02-08', 1680, 4);
"""


def _db_path() -> Path:
    path = Path(settings.database_url)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.executescript(SEED_SQL)
