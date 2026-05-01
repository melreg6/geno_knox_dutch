"""
test_integration.py
Full end-to-end verification of the GenoCAD -> Goldbar pipeline.

Runs every check in sequence and prints a final summary:
    1. Database conversion (row counts)
    2. Schema integrity (required tables exist)
    3. DNA sequence integrity
    4. Grammar rule extraction
    5. Parts extraction by category
    6. Goldbar translation (single cassette)
    7. Goldbar translation (multi-cassette)
    8. Validation against known published design (Switch LacI/TetR)
    9. Validation against known published design (Repressilator)

Run from the project root:
    python3 tests/test_integration.py
"""

import os
import sqlite3
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grammar_rule_engine.genocad_grammar_extractor import GenoCADGrammarExtractor
from grammar_rule_engine.goldbar_translator import translate_all

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'genocad', 'genocad.db')

# ── test result tracking ─────────────────────────────────────────────────────

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((status, name, detail))
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    return condition


def section(title):
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


# ── 1. DATABASE CONVERSION ───────────────────────────────────────────────────

def test_db_conversion():
    section("1. DATABASE CONVERSION: row counts")

    if not os.path.exists(DB_PATH):
        check("database file exists", False, f"not found at {DB_PATH}")
        return False

    check("database file exists", True, DB_PATH)

    expected = {
        "categories":       24,
        "parts":            54,
        "categories_parts": 54,
        "libraries":         2,
        "rules":             8,
        "rule_transform":   20,
        "grammars":          2,
    }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for table, exp in expected.items():
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            actual = cur.fetchone()[0]
            check(f"{table} row count", actual == exp,
                  f"{actual} rows (expected {exp})")
        except Exception as e:
            check(f"{table} row count", False, str(e))
    conn.close()
    return True


# ── 2. SCHEMA INTEGRITY ──────────────────────────────────────────────────────

def test_schema():
    section("2. SCHEMA: required tables present")

    required = [
        "categories", "parts", "categories_parts",
        "libraries", "rules", "rule_transform",
        "grammars", "library_part_join", "designs",
    ]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    present = {row[0] for row in cur.fetchall()}
    conn.close()

    for t in required:
        check(f"table '{t}' exists", t in present)


# ── 3. SEQUENCE INTEGRITY ────────────────────────────────────────────────────

def test_sequences():
    section("3. DNA SEQUENCE INTEGRITY")

    expected_lengths = {
        "a069g": 200,
        "a069h":  49,
        "a069i":  54,
        "a069m":  12,
        "a069n":  80,
    }

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for part_id, exp in expected_lengths.items():
        cur.execute("SELECT description, LENGTH(segment) FROM parts WHERE part_id = ?",
                    (part_id,))
        row = cur.fetchone()
        if row is None:
            check(f"{part_id} sequence length", False, "part not found")
            continue
        desc, actual = row
        check(f"{part_id} ({desc}) sequence length",
              actual == exp,
              f"{actual} bp (expected {exp})")
    conn.close()


# ── 4. GRAMMAR RULE EXTRACTION ───────────────────────────────────────────────

def test_grammar_rules():
    section("4. GRAMMAR RULE EXTRACTION")

    extractor = GenoCADGrammarExtractor(DB_PATH)
    rules = extractor.extract(grammar_id=1237)

    check("rules returned for grammar 1237", len(rules) > 0,
          f"{len(rules)} rules")

    rule_names = [r.name for r in rules]
    for expected_rule in ["1cas", "2cas", "3cas", "Transcription"]:
        check(f"rule '{expected_rule}' present", expected_rule in rule_names)

    # Transcription rule should have PRO, RBS, CDS, TER in order
    transcription = next((r for r in rules if r.name == "Transcription"), None)
    if transcription:
        letters = [c.letter for c in transcription.sequence]
        check("Transcription rule sequence = [PRO, RBS, CDS, TER]",
              letters == ["PRO", "RBS", "CDS", "TER"],
              f"got {letters}")


# ── 5. PARTS EXTRACTION ──────────────────────────────────────────────────────

def test_parts_extraction():
    section("5. PARTS EXTRACTION BY CATEGORY")

    extractor = GenoCADGrammarExtractor(DB_PATH)
    parts = extractor.extract_parts_by_category(grammar_id=1237)

    for cat in ["PRO", "RBS", "CDS", "TER"]:
        check(f"{cat} category present", cat in parts,
              f"{len(parts.get(cat, []))} parts")

    # Verify part structure
    if "PRO" in parts and parts["PRO"]:
        first = parts["PRO"][0]
        check("part dict has 'id' field", "id" in first)
        check("part dict has 'desc' field", "desc" in first)
        check("part dict has 'seq' field", "seq" in first)


# ── 6 & 7. GOLDBAR TRANSLATION ───────────────────────────────────────────────

def test_goldbar():
    section("6. GOLDBAR TRANSLATION: single cassette")

    extractor = GenoCADGrammarExtractor(DB_PATH)
    parts = extractor.extract_parts_by_category(grammar_id=1237)

    goldbar, categories = translate_all(parts, cassettes=1)
    check("single-cassette expression is 'PRO . RBS . CDS . TER'",
          goldbar == "PRO . RBS . CDS . TER",
          f"got '{goldbar}'")

    # Knox role mappings
    role_checks = {
        "PRO": "promoter",
        "RBS": "ribosomeBindingSite",
        "CDS": "cds",
        "TER": "terminator",
    }
    for cat, role in role_checks.items():
        check(f"{cat} mapped to Knox role '{role}'",
              cat in categories and role in categories[cat])

    section("7. GOLDBAR TRANSLATION: multi-cassette")
    goldbar2, _ = translate_all(parts, cassettes=2)
    check("multi-cassette wraps in 'one-or-more(...)'",
          goldbar2 == "one-or-more(PRO . RBS . CDS . TER)",
          f"got '{goldbar2}'")


# ── 8 & 9. KNOWN DESIGN VALIDATION ───────────────────────────────────────────

def test_known_designs():
    extractor = GenoCADGrammarExtractor(DB_PATH)
    parts = extractor.extract_parts_by_category(grammar_id=1237)

    role_map = {
        "PRO": "promoter",
        "RBS": "ribosomeBindingSite",
        "CDS": "cds",
        "TER": "terminator",
    }
    _, categories = translate_all(parts, cassettes=1)

    section("8. KNOWN DESIGN: Switch LacI/TetR (design_id 673)")
    # Structure: placI . RBS . tetR . B0010
    switch = {
        "PRO": "a069g",
        "RBS": "a069m",
        "CDS": "a069l",
        "TER": "a069n",
    }
    for cat, part_id in switch.items():
        role = role_map[cat]
        ids = categories.get(cat, {}).get(role, [])
        check(f"{cat}.{role} contains {part_id}", part_id in ids)

    section("9. KNOWN DESIGN: Repressilator (design_id 674)")
    # Uses placI, pcI, pTetR, tetR, cIts, lacI, RBS, B0010
    repressilator = {
        "PRO": ["a069g", "a069h", "a069i"],         # placI, pcI, pTetR
        "RBS": ["a069m"],                            # My_RBS
        "CDS": ["a069j", "a069k", "a069l"],         # cIts, lacI, tetR
        "TER": ["a069n"],                            # B0010
    }
    for cat, part_ids in repressilator.items():
        role = role_map[cat]
        available = categories.get(cat, {}).get(role, [])
        for pid in part_ids:
            check(f"{cat}.{role} contains {pid}", pid in available)


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print(" GENOCAD -> GOLDBAR INTEGRATION TEST")
    print("=" * 60)

    if not test_db_conversion():
        print("\nCannot continue: database missing. Run convert_to_db.py first.")
        return

    test_schema()
    test_sequences()
    test_grammar_rules()
    test_parts_extraction()
    test_goldbar()
    test_known_designs()

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" FINAL SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r[0] == "PASS")
    failed = sum(1 for r in results if r[0] == "FAIL")
    total = passed + failed

    print(f"\n  Total checks: {total}")
    print(f"  Passed:       {passed}")
    print(f"  Failed:       {failed}")

    if failed > 0:
        print("\n  Failed checks:")
        for status, name, detail in results:
            if status == "FAIL":
                print(f"    - {name}" + (f" ({detail})" if detail else ""))

    print("\n" + ("  ALL TESTS PASSED" if failed == 0 else "  SOME TESTS FAILED"))
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()