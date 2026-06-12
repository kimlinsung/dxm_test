import copy
import json
import unittest
from pathlib import Path

from starpick.schema import (
    SchemaError,
    validate_skeleton,
    validate_strategy,
    validate_transplant,
)

GOLDEN = Path(__file__).resolve().parent.parent / "fixtures" / "golden"


def load(name: str) -> dict:
    return json.loads((GOLDEN / name).read_text(encoding="utf-8"))


class SkeletonSchemaTest(unittest.TestCase):
    def test_golden_skeleton_passes(self):
        card = validate_skeleton(load("p1_skeleton.json"))
        self.assertEqual(card["hook"]["type"], "反常识宣言")

    def test_missing_hook_rejected(self):
        card = load("p1_skeleton.json")
        del card["hook"]
        with self.assertRaisesRegex(SchemaError, "hook"):
            validate_skeleton(card)

    def test_empty_structure_rejected(self):
        card = load("p1_skeleton.json")
        card["structure"] = []
        with self.assertRaisesRegex(SchemaError, "structure"):
            validate_skeleton(card)

    def test_invalid_hook_seconds_rejected(self):
        card = load("p1_skeleton.json")
        card["hook"]["end"] = 0
        with self.assertRaisesRegex(SchemaError, "start/end"):
            validate_skeleton(card)

    def test_non_dict_rejected(self):
        with self.assertRaises(SchemaError):
            validate_skeleton(["not", "a", "dict"])


class StrategySchemaTest(unittest.TestCase):
    def test_golden_strategy_passes(self):
        strategy = validate_strategy(load("p2_strategy.json"))
        self.assertEqual(strategy["transferability"], 86)

    def test_transferability_range_enforced(self):
        strategy = load("p2_strategy.json")
        strategy["transferability"] = 130
        with self.assertRaisesRegex(SchemaError, "0-100"):
            validate_strategy(strategy)

    def test_replace_item_fields_enforced(self):
        strategy = load("p2_strategy.json")
        broken = copy.deepcopy(strategy)
        del broken["replace"][0]["reason"]
        with self.assertRaisesRegex(SchemaError, "replace"):
            validate_strategy(broken)


class TransplantSchemaTest(unittest.TestCase):
    def test_golden_transplant_passes(self):
        text = (GOLDEN / "p3_transplant.md").read_text(encoding="utf-8")
        self.assertEqual(validate_transplant(text), text)

    def test_missing_section_rejected(self):
        with self.assertRaisesRegex(SchemaError, "分镜表"):
            validate_transplant("### 口播脚本\n只有一半的产出")


if __name__ == "__main__":
    unittest.main()
