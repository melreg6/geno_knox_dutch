# db.py
import sqlite3
from config import DB_PATH, SKIP_LETTERS

def load_parts():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT c.description as cat, c.letter, p.part_id as id, p.description as desc
        FROM categories c
        JOIN categories_parts cp ON c.category_id = cp.category_id
        JOIN parts p ON p.id = cp.part_id
        WHERE c.letter NOT IN ('S','[',']','(',')','{{','}}','CAS','TP')
        ORDER BY c.description, p.part_id
    """)

    parts = {}
    for row in cur.fetchall():
        if row["letter"] in SKIP_LETTERS:
            continue
        parts.setdefault(row["cat"], []).append({
            "id": row["id"],
            "desc": row["desc"] or ""
        })

    conn.close()
    return parts