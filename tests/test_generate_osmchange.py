from unittest import TestCase

from src.models.generate_osmchange import OsmChangeGenerator, OSMRelation


class TestOsmChangeGenerator(TestCase):
    def setUp(self):
        self.gen = OsmChangeGenerator()

    def test_classify_already_tagged(self):
        relation = OSMRelation(
            osm_id=12345, version=7, tags={"wikidata": "Q12345", "name": "Test"}
        )
        result = self.gen.__classify__("Q12345", relation)
        self.assertEqual(result, "skip")
        self.assertEqual(self.gen.already_tagged_count, 1)
        self.assertEqual(len(self.gen.modify_blocks), 0)

    def test_classify_missing_tag_will_patch(self):
        relation = OSMRelation(
            osm_id=12345, version=7, tags={"name": "Test", "route": "hiking"}
        )
        result = self.gen.__classify__("Q12345", relation)
        self.assertEqual(result, "patch")
        self.assertEqual(self.gen.patched_count, 1)
        self.assertEqual(len(self.gen.modify_blocks), 1)

    def test_classify_mismatch_will_not_patch(self):
        relation = OSMRelation(
            osm_id=12345, version=7, tags={"wikidata": "Q99999", "name": "Test"}
        )
        result = self.gen.__classify__("Q12345", relation)
        self.assertEqual(result, "mismatch")
        self.assertEqual(self.gen.mismatch_count, 1)
        self.assertEqual(len(self.gen.modify_blocks), 0)
        self.assertIn((12345, "Q12345", "Q99999"), self.gen.mismatches)

    def test_patch_block_contains_wikidata_tag(self):
        relation = OSMRelation(
            osm_id=12345, version=7, tags={"name": "Test", "route": "hiking"}
        )
        self.gen.__classify__("Q12345", relation)
        block = self.gen.modify_blocks[0]
        tags = {child.get("k"): child.get("v") for child in block.findall(".//tag")}
        self.assertEqual(tags.get("wikidata"), "Q12345")
        self.assertEqual(tags.get("name"), "Test")
        self.assertEqual(tags.get("route"), "hiking")
