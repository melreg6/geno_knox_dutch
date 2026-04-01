from genocad_grammar_extractor import GrammarRule, PartCategory


class GoldbarTranslator:

    def translate(self, rule: GrammarRule) -> str:
        tokens = [self._encode_category(cat) for cat in rule.sequence]
        return " . ".join(tokens)

    def _encode_category(self, cat: PartCategory) -> str:
        token = cat.name
        if cat.repeatable:
            token = f"{token}+"
        if cat.optional:
            token = f"[{token}]"
        return token

    def translate_all(self, rules: list[GrammarRule]) -> dict[str, str]:
        return {rule.name: self.translate(rule) for rule in rules}


# ── Example output ─────────────────────────────────────────────
# standard_construct   → "promoter . rbs . cds+ . terminator"
# insulated_construct  → "[insulator] . promoter . rbs . cds+ . terminator . [insulator]"
