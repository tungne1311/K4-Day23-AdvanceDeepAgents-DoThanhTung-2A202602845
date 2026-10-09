import json
import unittest

from prepare_sources import evidence_notes, plan_for_sources


class SourcePreparationTests(unittest.TestCase):
    def test_plans_actual_discovery_tool_for_each_source_family(self):
        sources = [{"source": family, "title": "Paper: title", "id": "id", "url": "https://example.org/paper"}
                   for family in ("arxiv", "hf-search", "hf-daily", "web")]
        plan = plan_for_sources(sources)
        self.assertEqual([step[0] for step in plan], ["arxiv_search", "hf_search_papers", "hf_daily_papers", "web_search"])
        self.assertEqual(plan[-1][1]["query"], "https://example.org/paper")

    def test_notes_copy_returned_evidence_without_synthesizing_claims(self):
        record = {"title": "Actual title", "id": "1", "url": "https://huggingface.co/papers/1",
                  "published": "2026-01-01", "summary": "Exact retrieved evidence", "source": "wrong"}
        text = evidence_notes("hf_search_papers", json.dumps([record]), "1")
        self.assertIn("Exact retrieved evidence", text)
        self.assertIn("- source: hf-search", text)
        self.assertNotIn("- source: wrong", text)

    def test_does_not_convert_failed_tools_to_evidence(self):
        for result in ("NO RESULTS", "ERROR: timeout"):
            self.assertEqual(evidence_notes("web_search", result), "")

    def test_prefers_exact_requested_id_over_unrelated_results(self):
        records = [{"title": title, "id": identifier, "url": "https://arxiv.org/abs/" + identifier, "summary": "excerpt"}
                   for title, identifier in (("unrelated", "2"), ("target", "1"))]
        notes = evidence_notes("arxiv_search", json.dumps(records), "1")
        self.assertIn("target", notes)
        self.assertNotIn("unrelated", notes)
