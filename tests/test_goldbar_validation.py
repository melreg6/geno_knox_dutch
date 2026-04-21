"""
test_goldbar_validation.py
Validates that translate_all() produces correct Goldbar expressions from
extracted GenoCAD parts.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grammar_rule_engine.genocad_grammar_extractor import GenoCADGrammarExtractor
from grammar_rule_engine.goldbar_translator import translate_all

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'genocad', 'genocad.db')


def main():
    extractor = GenoCADGrammarExtractor(DB_PATH)
    parts = extractor.extract_parts_by_category(grammar_id=1237)

    print("=== GOLDBAR TRANSLATOR VALIDATION ===\n")

    # Test 1: single cassette
    goldbar, categories = translate_all(parts, cassettes=1)
    print("Single cassette")
    print(f"  Goldbar: {goldbar}")
    print(f"  Categories: {list(categories.keys())}")

    all_good = True

    expected_expr = "PRO . RBS . CDS . TER"
    if goldbar == expected_expr:
        print(f"  [PASS] expression matches expected: {expected_expr}")
    else:
        print(f"  [FAIL] expected '{expected_expr}', got '{goldbar}'")
        all_good = False

    # Check each category has Knox-compatible roles
    expected_roles = {
        "PRO": "promoter",
        "RBS": "ribosomeBindingSite",
        "CDS": "cds",
        "TER": "terminator",
    }
    for cat, role in expected_roles.items():
        if cat in categories and role in categories[cat]:
            n = len(categories[cat][role])
            print(f"  [PASS] {cat} -> {role} ({n} parts)")
        else:
            print(f"  [FAIL] {cat} missing or wrong role")
            all_good = False

    # Test 2: multi-cassette
    print("\nMulti-cassette (2+)")
    goldbar2, _ = translate_all(parts, cassettes=2)
    print(f"  Goldbar: {goldbar2}")
    expected2 = "one-or-more(PRO . RBS . CDS . TER)"
    if goldbar2 == expected2:
        print(f"  [PASS] expression matches expected: {expected2}")
    else:
        print(f"  [FAIL] expected '{expected2}', got '{goldbar2}'")
        all_good = False

    # Test 3: validate against known design "Switch LacI/TetR"
    # placI (a069g) must be in PRO list, tetR (a069l) must be in CDS list, etc.
    print("\nKnown design parts present in Goldbar categories")
    known = {
        "PRO": "a069g",   # placI
        "RBS": "a069m",   # My_RBS
        "CDS": "a069l",   # tetR
        "TER": "a069n",   # B0010
    }
    for cat, part_id in known.items():
        role = expected_roles[cat]
        if part_id in categories.get(cat, {}).get(role, []):
            print(f"  [PASS] {cat}.{role} contains {part_id}")
        else:
            print(f"  [FAIL] {cat}.{role} missing {part_id}")
            all_good = False

    print("\n" + ("ALL CHECKS PASSED" if all_good else "SOME CHECKS FAILED"))


if __name__ == '__main__':
    main()