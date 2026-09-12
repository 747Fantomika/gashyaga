import aiosqlite
from datetime import datetime

DB_PATH = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT,
                service TEXT NOT NULL,
                price TEXT NOT NULL,
                contact TEXT NOT NULL,
                comment TEXT,
                status TEXT DEFAULT 'new',
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def add_order(user_id, username, full_name, service, price, contact, comment):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO orders (user_id, username, full_name, service, price, contact, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, full_name, service, price, contact, comment,
              datetime.now().strftime("%Y-%m-%d %H:%M")))
        await db.commit()
        return cursor.lastrowid

async def get_order(order_id):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

async def get_user_orders(user_id, limit=10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def get_new_orders(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE status = 'new' ORDER BY id ASC LIMIT ?",
            (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

async def set_status(order_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM orders") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'") as cur:
            new = (await cur.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM orders WHERE status = 'done'") as cur:
            done = (await cur.fetchone())[0]
        return {"total": total, "new": new, "done": done}
