import sqlite3
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartCategory:
    name: str
    genocad_id: str
    optional: bool = False
    repeatable: bool = False


@dataclass
class GrammarRule:
    name: str
    sequence: list[PartCategory] = field(default_factory=list)


class GenoCADGrammarExtractor:

    def __init__(self, db_path: str):
        self.db_path = db_path

    def extract(self) -> list[GrammarRule]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM grammar_rules")
        rules_raw = cursor.fetchall()
        rules = []

        for rule_id, rule_name in rules_raw:
            cursor.execute("""
                SELECT pc.id, pc.name, rp.optional, rp.repeatable
                FROM rule_parts rp
                JOIN part_categories pc
                  ON rp.part_category_id = pc.id
                WHERE rp.rule_id = ?
                ORDER BY rp.position ASC
            """, (rule_id,))

            sequence = [
                PartCategory(
                    name=name,
                    genocad_id=cat_id,
                    optional=bool(optional),
                    repeatable=bool(repeatable)
                )
                for cat_id, name, optional, repeatable in cursor.fetchall()
            ]

            rules.append(GrammarRule(name=rule_name, sequence=sequence))

        conn.close()
        return rules
