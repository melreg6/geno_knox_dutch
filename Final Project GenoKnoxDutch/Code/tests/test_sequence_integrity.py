"""
test_sequence_integrity.py
Verifies that DNA sequences (the `segment` column in `parts`) were loaded
intact by checking sequence lengths against the actual values from the
original SQL dump.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'genocad', 'genocad.db')

# Correct sequence lengths from the original SQL dump (grammar 1237 parts)
EXPECTED_LENGTHS = {
    "a069g": 200,    # placI
    "a069h":  49,    # pcI
    "a069i":  54,    # pTetR
    "a069m":  12,    # My_RBS
    "a069n":  80,    # B0010
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=== DNA SEQUENCE INTEGRITY CHECK ===\n")
    all_good = True

    for part_id, expected_len in EXPECTED_LENGTHS.items():
        cur.execute(
            "SELECT description, LENGTH(segment) FROM parts WHERE part_id = ?",
            (part_id,)
        )
        row = cur.fetchone()

        if row is None:
            print(f"  [FAIL] {part_id}: not found in DB")
            all_good = False
            continue

        desc, actual_len = row
        status = "PASS" if actual_len == expected_len else "FAIL"
        if actual_len != expected_len:
            all_good = False
        print(f"  [{status}] {part_id} ({desc}): "
              f"{actual_len} bp (expected {expected_len})")

    print("\n" + ("ALL CHECKS PASSED" if all_good else "SOME CHECKS FAILED"))
    conn.close()


if __name__ == '__main__':
    main()