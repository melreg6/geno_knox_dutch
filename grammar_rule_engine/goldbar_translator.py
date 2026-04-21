"""
goldbar_translator.py
Translates extracted GenoCAD parts into Goldbar expressions for Knox.
"""

ROLE_MAP = {
    "PRO": "promoter",
    "RBS": "ribosomeBindingSite",
    "CDS": "cds",
    "TER": "terminator",
}

ORDER = ["PRO", "RBS", "CDS", "TER"]


def translate_all(parts: dict, cassettes: int = 1) -> tuple[str, dict]:
    """
    Convert extracted parts into a Goldbar expression and category map for Knox.

    Args:
        parts:      output of GenoCADGrammarExtractor.extract_parts_by_category()
                    i.e. { "PRO": [{"id": "a069g", ...}, ...], "RBS": [...], ... }
        cassettes:  1 for a single transcription unit, >1 for one-or-more.

    Returns:
        (goldbar_string, categories_dict) where
            goldbar_string is a Knox-compatible expression, e.g.
                "PRO . RBS . CDS . TER"
            categories_dict maps each token to its role and part IDs, e.g.
                { "PRO": { "promoter": ["a069g", "a069h"] }, ... }
    """
    active = [r for r in ORDER if r in parts and len(parts[r]) > 0]
    if not active:
        return None, None

    tokens = []
    categories = {}

    for role in active:
        knox_role = ROLE_MAP.get(role, "cds")
        categories[role] = {
            knox_role: [p["id"] for p in parts[role]]
        }
        tokens.append(role)

    expr = " . ".join(tokens)
    goldbar = f"one-or-more({expr})" if cassettes > 1 else expr

    return goldbar, categories