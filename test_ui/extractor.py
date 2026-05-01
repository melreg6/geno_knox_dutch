import sqlite3
from dataclasses import dataclass, field

SKIP_LETTERS = {"S", "[", "]", "(", ")", "{", "}", "CAS", "TP"}
DISPLAY_ORDER = ["Promoter", "Ribosome", "Coding sequence", "Terminator"]

@dataclass
class Part:
    id: str
    desc: str
    seq: str
    letter: str

@dataclass
class CategoryParts:
    name: str
    letter: str
    grammar_id: int
    parts: list[Part] = field(default_factory=list)


def load_parts(db_path: str, grammar_id: int = None) -> dict[str, CategoryParts]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT c.description AS cat, c.letter, c.grammar_id,
               p.part_id AS id, p.description AS desc, p.segment AS seq
        FROM categories c
        JOIN categories_parts cp ON c.category_id = cp.category_id
        JOIN parts p ON p.id = cp.part_id
    """
    params = []
    if grammar_id is not None:
        query += " WHERE c.grammar_id = ?"
        params.append(grammar_id)
    query += " ORDER BY c.description, p.part_id"

    cur.execute(query, params)

    result = {}
    for row in cur.fetchall():
        if row["letter"] in SKIP_LETTERS:
            continue
        cat_name = row["cat"]
        if cat_name not in result:
            result[cat_name] = CategoryParts(
                name=cat_name,
                letter=row["letter"],
                grammar_id=row["grammar_id"],
            )
        result[cat_name].parts.append(Part(
            id=row["id"],
            desc=row["desc"] or "",
            seq=row["seq"] or "",
            letter=row["letter"],
        ))

    conn.close()
    return result


def parts_for_ui(db_path: str, grammar_id: int = None) -> dict:
    raw = load_parts(db_path, grammar_id)
    return {
        name: [{"id": p.id, "desc": p.desc} for p in cp.parts]
        for name, cp in raw.items()
    }


if __name__ == "__main__":
    import os, sys
    db = os.path.join(os.path.dirname(__file__), "..", "geno_knox_dutch", "genocad.db")
    if not os.path.exists(db):
        print(f"DB not found at {db}")
        sys.exit(1)

    cats = load_parts(db)
    for name, cp in cats.items():
        print(f"[{cp.letter}] {name} — {len(cp.parts)} parts (grammar {cp.grammar_id})")
        for p in cp.parts[:3]:
            print(f"    {p.id}  {p.desc[:40]}")
        if len(cp.parts) > 3:
            print(f"    ... +{len(cp.parts)-3} more")