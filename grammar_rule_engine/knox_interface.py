import json
import requests
from dataclasses import dataclass, asdict

from genocad_grammar_extractor import GenoCADGrammarExtractor
from goldbar_translator import GoldbarTranslator

KNOX_API_URL = "http://your-knox-host/api"   # <- swap in real URL


@dataclass
class KnoxRule:
    name: str
    goldbar: str
    categories: list[str]


@dataclass
class KnoxPayload:
    rules: list[KnoxRule]
    version: str = "1.0"


class KnoxClient:

    def __init__(self, base_url: str = KNOX_API_URL):
        self.base_url = base_url

    def submit_rules(self, payload: KnoxPayload) -> dict:
        """POST Goldbar rules to Knox."""
        response = requests.post(
            f"{self.base_url}/rules",
            json=asdict(payload),
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def enumerate_designs(self, rule_name: str) -> dict:
        """Ask Knox to enumerate all valid designs for a given rule."""
        response = requests.get(
            f"{self.base_url}/enumerate",
            params={"rule": rule_name}
        )
        response.raise_for_status()
        return response.json()

    def get_rule(self, rule_name: str) -> dict:
        """Fetch a previously submitted rule from Knox."""
        response = requests.get(
            f"{self.base_url}/rules/{rule_name}"
        )
        response.raise_for_status()
        return response.json()


def run_pipeline(db_path: str) -> dict:
    """
    Full pipeline:
    1. Extract grammar from GenoCAD DB
    2. Translate to Goldbar
    3. Submit to Knox
    4. Return enumerated designs
    """
    # Step 1 - extract
    rules = GenoCADGrammarExtractor(db_path).extract()

    # Step 2 - translate
    translations = GoldbarTranslator().translate_all(rules)

    knox_rules = [
        KnoxRule(
            name=rule.name,
            goldbar=translations[rule.name],
            categories=[cat.name for cat in rule.sequence]
        )
        for rule in rules
    ]
    payload = KnoxPayload(rules=knox_rules)

    # Step 3 - submit to Knox
    client = KnoxClient()
    submit_response = client.submit_rules(payload)
    print(f"Knox accepted rules: {submit_response}")

    # Step 4 - enumerate designs for each rule
    results = {}
    for rule in knox_rules:
        designs = client.enumerate_designs(rule.name)
        results[rule.name] = designs
        print(f"{rule.name}: {len(designs.get('designs', []))} designs found")

    return results


if __name__ == "__main__":
    results = run_pipeline("genocad.db")
    print(json.dumps(results, indent=2))
