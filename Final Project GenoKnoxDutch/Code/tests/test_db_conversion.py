"""
test_db_conversion.py
Verifies that the SQLite DB was converted correctly from the MySQL dump
by checking table row counts against the known values.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'genocad', 'genocad.db')

EXPECTED_COUNTS = {
    "categories":       24,
    "parts":            54,
    "categories_parts": 54,
    "libraries":         2,
    "rules":             8,
    "rule_transform":   20,
    "grammars":          2,
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        print("Run convert_to_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=== DATABASE ROW COUNT VALIDATION ===\n")
    all_good = True
    for table, expected in EXPECTED_COUNTS.items():
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            actual = cur.fetchone()[0]
            status = "PASS" if actual == expected else "FAIL"
            if actual != expected:
                all_good = False
            print(f"  [{status}] {table}: {actual} rows (expected {expected})")
        except Exception as e:
            all_good = False
            print(f"  [FAIL] {table}: ERROR - {e}")

    print("\n" + ("ALL CHECKS PASSED" if all_good else "SOME CHECKS FAILED"))
    conn.close()


if __name__ == '__main__':
    main()