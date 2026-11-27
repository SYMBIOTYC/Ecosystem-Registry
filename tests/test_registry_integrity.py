import csv
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CanonicalRegistryIntegrityTests(unittest.TestCase):
    def test_asset_csv_has_stable_unique_ids_and_thirteen_columns(self):
        with (ROOT / "registry" / "records.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 69)
        self.assertTrue(all(len(row) == 13 for row in rows))
        ids = [row["id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(row["id"] and row["name"] and row["type"] for row in rows))

    def test_partner_catalog_and_tools_are_separate_asset_records(self):
        with (ROOT / "registry" / "records.csv").open(encoding="utf-8", newline="") as stream:
            rows = {row["id"]: row for row in csv.DictReader(stream)}
        self.assertEqual(rows["CATALOG-AWESOME-SELFHOSTED"]["type"], "Integration")
        for tool_id in [
            "TOOL-SEARXNG",
            "TOOL-MEILISEARCH",
            "TOOL-OPENSEARCH",
            "TOOL-OLLAMA",
            "TOOL-OPEN-WEBUI",
            "TOOL-FORGEJO",
        ]:
            self.assertEqual(rows[tool_id]["type"], "Tool")
            self.assertEqual(rows[tool_id]["parent_id"], "CATALOG-AWESOME-SELFHOSTED")
            self.assertIn("not verified", rows[tool_id]["evidence_note"].lower())

    def test_tool_registry_references_resolve_and_remain_non_callable(self):
        registry = yaml.safe_load((ROOT / "registry" / "tools.yaml").read_text(encoding="utf-8"))
        tools = {tool["id"]: tool for tool in registry["tools"]}
        skills = {skill["id"]: skill for skill in registry["skills"]}
        self.assertEqual(len(tools), 6)
        self.assertEqual(len(skills), 5)
        self.assertEqual(registry["catalog_sources"][0]["data_revision"], "11bb4605f128bdf6f759bdbcb4eebb1876349f14")
        invocation_ids = set()
        for tool in tools.values():
            self.assertEqual(tool["status"], "discovered")
            self.assertEqual(tool["deployment_status"], "unverified")
            for invocation in tool["invocations"]:
                self.assertEqual(invocation["status"], "contract_only")
                self.assertNotIn(invocation["id"], invocation_ids)
                invocation_ids.add(invocation["id"])
        self.assertEqual(len(invocation_ids), 12)

        for skill in skills.values():
            self.assertEqual(skill["status"], "proposed")
            for tool_id in skill.get("requires_tools", []):
                self.assertIn(tool_id, tools)
            for tool_id in skill.get("requires_any_tools", []):
                self.assertIn(tool_id, tools)
            referenced = list(skill.get("requires_invocations", []))
            for invocation_set in skill.get("invocation_sets", []):
                self.assertIn(invocation_set["tool"], tools)
                referenced.extend(invocation_set["invocations"])
            known = {inv["id"] for tool in tools.values() for inv in tool["invocations"]}
            self.assertTrue(set(referenced).issubset(known))

    def test_snapshot_counts_match_asset_inventory(self):
        counts = (ROOT / "registry" / "counts.md").read_text(encoding="utf-8")
        self.assertIn("**Total repository records** | **82**", counts)
        self.assertIn("**Total** | **69**", counts)


if __name__ == "__main__":
    unittest.main()
