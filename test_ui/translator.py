ROLE_MAP = {
    "Promoter":        "promoter",
    "Ribosome":        "ribosomeBindingSite",
    "Coding sequence": "cds",
    "Terminator":      "terminator",
    "Insulator":       "insulator",
    "Spacer":          "spacer",
}

ORDER = ["Promoter", "Ribosome", "Coding sequence", "Terminator"]


def _sanitize_token(cat_name: str) -> str:
    token = "".join(c if c.isalnum() else "_" for c in cat_name)
    return token.strip("_")


def build_goldbar(selected: dict, cassettes: int = 1):
    ordered = [c for c in ORDER if c in selected and selected[c]]
    extras  = sorted(c for c in selected if c not in ORDER and selected[c])
    active  = ordered + extras

    if not active:
        return None, None

    tokens     = []
    categories = {}
    for cat in active:
        tok  = _sanitize_token(cat)
        role = ROLE_MAP.get(cat, "cds")
        categories[tok] = {role: list(selected[cat])}
        tokens.append(tok)

    expr    = " . ".join(tokens)
    goldbar = f"one-or-more({expr})" if cassettes > 1 else expr
    return goldbar, categories


if __name__ == "__main__":
    test = {
        "Promoter":        ["a069g", "a069h"],
        "Ribosome":        ["r001"],
        "Coding sequence": ["c001"],
        "Terminator":      ["t001"],
    }
    gb, cats = build_goldbar(test, cassettes=1)
    print("Single cassette:", gb)
    gb, cats = build_goldbar(test, cassettes=2)
    print("Multi cassette: ", gb)
    gb, cats = build_goldbar({})
    print("Empty:          ", gb)
