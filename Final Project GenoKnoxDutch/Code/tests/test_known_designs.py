"""
test_known_designs.py
Validates the extractor against a known-valid published design from GenoCAD:
    "Switch LacI/TetR" (design_id = 673)

Structure: placI . My_RBS . tetR . B0010

If the extractor finds all four parts in the right categories, the pipeline
is correctly reading the GenoCAD database.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grammar_rule_engine.genocad_grammar_extractor import GenoCADGrammarExtractor

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'genocad', 'genocad.db')


def main():
    extractor = GenoCADGrammarExtractor(DB_PATH)
    parts = extractor.extract_parts_by_category(grammar_id=1237)

    # Known valid design: Switch LacI/TetR
    expected_parts = {
        "PRO": ["a069g"],   # placI
        "RBS": ["a069m"],   # My_RBS
        "CDS": ["a069l"],   # tetR
        "TER": ["a069n"],   # B0010
    }

    print("=== VALIDATING AGAINST KNOWN DESIGN: Switch LacI/TetR ===\n")

    all_good = True
    for category, required_ids in expected_parts.items():
        if category not in parts:
            print(f"  [FAIL] {category}: category missing entirely")
            all_good = False
            continue

        found_ids = [p["id"] for p in parts[category]]
        for req in required_ids:
            if req in found_ids:
                print(f"  [PASS] {category}: found {req}")
            else:
                print(f"  [FAIL] {category}: MISSING {req} "
                      f"(found: {found_ids})")
                all_good = False

    print("\n" + ("ALL CHECKS PASSED" if all_good else "SOME CHECKS FAILED"))


if __name__ == '__main__':
    main()