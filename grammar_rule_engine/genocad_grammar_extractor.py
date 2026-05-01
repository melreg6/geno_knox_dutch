import sqlite3
from dataclasses import dataclass, field

SKIP_LETTERS = {"S", "[", "]", "(", ")", "{", "}", "CAS", "TP"}


@dataclass
class PartCategory:
    letter: str
    description: str
    category_id: int
    grammar_id: int


@dataclass
class GrammarRule:
    name: str
    rule_id: int
    grammar_id: int
    sequence: list[PartCategory] = field(default_factory=list)


class GenoCADGrammarExtractor:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def extract(self, grammar_id: int = None) -> list[GrammarRule]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT r.rule_id, r.code as rule_name, r.grammar_id
            FROM rules r
        """
        params = []
        if grammar_id:
            query += " WHERE r.grammar_id = ?"
            params.append(grammar_id)

        cursor.execute(query, params)
        rules_raw = cursor.fetchall()
        rules = []

        for row in rules_raw:
            cursor.execute("""
                SELECT c.category_id, c.letter, c.description, c.grammar_id
                FROM rule_transform rt
                JOIN categories c ON rt.category_id = c.category_id
                WHERE rt.rule_id = ?
                ORDER BY rt.transform_order ASC
            """, (row["rule_id"],))

            sequence = [
                PartCategory(
                    letter=r["letter"],
                    description=r["description"],
                    category_id=r["category_id"],
                    grammar_id=r["grammar_id"]
                )
                for r in cursor.fetchall()
                if r["letter"] not in SKIP_LETTERS
            ]

            rules.append(GrammarRule(
                name=row["rule_name"],
                rule_id=row["rule_id"],
                grammar_id=row["grammar_id"],
                sequence=sequence
            ))

        conn.close()
        return rules

    def extract_parts_by_category(self, grammar_id: int = None) -> dict:
        """
        Returns { "PRO": [{"id": "a069g", "desc": "placI", "seq": "..."}], ... }
        Keyed by category letter (PRO, RBS, CDS, TER).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT c.letter, p.part_id as id, p.description as desc, p.segment as seq
            FROM categories c
            JOIN categories_parts cp ON c.category_id = cp.category_id
            JOIN parts p ON p.id = cp.part_id
            WHERE cp.user_id = 0
        """
        params = []
        if grammar_id:
            query += " AND c.grammar_id = ?"
            params.append(grammar_id)

        query += " ORDER BY c.letter, p.part_id"
        cursor.execute(query, params)

        parts = {}
        for row in cursor.fetchall():
            letter = row["letter"]
            if letter in SKIP_LETTERS:
                continue
            parts.setdefault(letter, []).append({
                "id": row["id"],
                "desc": row["desc"] or "",
                "seq": row["seq"] or ""
            })

        conn.close()
        return parts