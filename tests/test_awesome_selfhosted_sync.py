import io
import tarfile
import unittest

from tools.awesome_selfhosted_sync import (
    CatalogError,
    parse_catalog_archive,
    serialize_catalog,
    validate_revision,
)


REVISION = "11bb4605f128bdf6f759bdbcb4eebb1876349f14"


def make_archive(files):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(f"awesome-selfhosted-data-{REVISION}/{path}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class AwesomeSelfhostedSyncTests(unittest.TestCase):
    def test_requires_full_immutable_git_revision(self):
        with self.assertRaises(CatalogError):
            validate_revision("master")
        with self.assertRaises(CatalogError):
            validate_revision("11bb460")

    def test_normalizes_yaml_records_without_granting_execution(self):
        archive = make_archive({
            "software/searxng.yml": """
name: SearXNG
description: Metasearch engine
website_url: https://docs.searxng.org/
source_code_url: https://github.com/searxng/searxng/
licenses: [AGPL-3.0]
platforms: [Python, Docker]
tags: [Search Engines]
archived: false
""",
            "software/ollama.yml": """
name: Ollama
description: Local model runtime
source_code_url: https://github.com/ollama/ollama
licenses: [MIT]
platforms: [Docker]
tags: [GenAI]
archived: false
""",
            "platforms/docker.yml": "name: Docker\n",
        })
        records = parse_catalog_archive(archive, REVISION)
        self.assertEqual([item["catalog_id"] for item in records], [
            "awesome-selfhosted:ollama",
            "awesome-selfhosted:searxng",
        ])
        self.assertEqual(records[1]["source_code_url"], "https://github.com/searxng/searxng/")
        self.assertEqual(records[1]["lifecycle_status"], "discovered")
        self.assertEqual(records[1]["invocation_status"], "not_authorized")
        self.assertEqual(records[1]["catalog_license"], "CC-BY-SA-3.0")

    def test_rejects_duplicate_stable_ids(self):
        archive = make_archive({
            "software/search.yml": "name: Search\n",
            "software/search-copy.yml": "name: Search copy\n",
        })
        with self.assertRaises(CatalogError):
            parse_catalog_archive(archive, REVISION)

    def test_rejects_missing_required_name(self):
        archive = make_archive({"software/missing-name.yml": "description: Missing\n"})
        with self.assertRaises(CatalogError):
            parse_catalog_archive(archive, REVISION)

    def test_rejects_non_https_external_urls(self):
        archive = make_archive({
            "software/bad.yml": """
name: Bad
website_url: http://example.com
source_code_url: https://github.com/example/bad
"""
        })
        with self.assertRaises(CatalogError):
            parse_catalog_archive(archive, REVISION)

    def test_serialization_is_deterministic_and_attributed(self):
        archive = make_archive({"software/example.yml": "name: Example\n"})
        records = parse_catalog_archive(archive, REVISION)
        first = serialize_catalog(records, REVISION)
        second = serialize_catalog(records, REVISION)
        self.assertEqual(first, second)
        self.assertIn('"catalog_license":"CC-BY-SA-3.0"', first)
        self.assertIn('"source_revision":"' + REVISION + '"', first)
        self.assertIn("awesome-selfhosted-data", first)

    def test_rejects_oversized_archive(self):
        from tools.awesome_selfhosted_sync import MAX_ARCHIVE_BYTES
        with self.assertRaises(CatalogError):
            parse_catalog_archive(b"x" * (MAX_ARCHIVE_BYTES + 1), REVISION)


if __name__ == "__main__":
    unittest.main()
