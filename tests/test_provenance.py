import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from provenance import SourceLedger
from research import ResearchProgress


class ProvenanceTests(unittest.TestCase):
    def test_cannot_relabel_arxiv_as_hf(self):
        ledger = SourceLedger()
        ledger.record("arxiv_search", json.dumps([{"url": "https://arxiv.org/abs/2302.04761"}]))
        with self.assertRaisesRegex(RuntimeError, "claimed discovery tools"):
            ledger.validate([{"n": 1, "source": "hf-search", "url": "https://huggingface.co/papers/2302.04761"}])

    def test_daily_and_search_are_distinct(self):
        ledger = SourceLedger()
        url = "https://huggingface.co/papers/2302.04761"
        ledger.record("hf_search_papers", json.dumps([{"url": url, "source": "hf-daily"}]))
        ledger.validate([{"n": 1, "source": "hf-search", "url": url}])
        with self.assertRaises(RuntimeError):
            ledger.validate([{"n": 1, "source": "hf-daily", "url": url}])

    def test_fetch_is_not_discovery(self):
        ledger = SourceLedger()
        ledger.record("web_fetch", "URL: https://example.org/paper")
        self.assertEqual(ledger.records(), [])

    def test_failures_and_malformed_records_do_not_count(self):
        ledger = SourceLedger()
        for tool, content in [("web_search", "ERROR: failed https://example.org"),
                              ("arxiv_search", "NO RESULTS"), ("hf_daily_papers", "invalid JSON")]:
            ledger.record(tool, content)
        self.assertEqual(ledger.records(), [])

    def test_web_urls_are_preserved(self):
        ledger = SourceLedger()
        url = "https://arxiv.org/html/2609.37196"
        ledger.record("web_search", f"Source ({url}).")
        ledger.validate([{"n": 1, "source": "web", "url": url}])
        self.assertEqual(ledger.records(), [{"source": "web", "url": url}])

    def test_callback_keeps_parallel_tool_results_separate(self):
        ledger = SourceLedger()
        progress = ResearchProgress(ledger)
        progress.on_tool_start({"name": "hf_search_papers"}, "", run_id="a")
        progress.on_tool_start({"name": "arxiv_search"}, "", run_id="b")
        progress.on_tool_end(SimpleNamespace(content='[{"url":"https://arxiv.org/abs/1"}]'), run_id="b")
        progress.on_tool_end('[{"url":"https://huggingface.co/papers/2"}]', run_id="a")
        self.assertEqual(ledger.records(), [{"source": "arxiv", "url": "https://arxiv.org/abs/1"},
                                          {"source": "hf-search", "url": "https://huggingface.co/papers/2"}])

    def test_missing_source_is_rejected(self):
        with self.assertRaises(RuntimeError):
            SourceLedger().validate([{"n": 1, "source": "web", "url": "https://example.org"}])

    @patch("research.upload")
    def test_agent_snapshot_is_written_from_host_observations(self, upload):
        ledger = SourceLedger()
        progress = ResearchProgress(ledger, backend=object())
        progress.on_tool_start({"name": "hf_search_papers"}, "", run_id="a")
        progress.on_tool_end('[{"url":"https://huggingface.co/papers/2"}]', run_id="a")
        payload = upload.call_args.args[1]
        self.assertEqual(json.loads(next(iter(payload.values()))), ledger.records())

    @patch("research.upload", side_effect=OSError("upload failed"))
    def test_snapshot_failure_does_not_erase_authoritative_evidence(self, upload):
        ledger = SourceLedger()
        progress = ResearchProgress(ledger, backend=object())
        progress.on_tool_start({"name": "arxiv_search"}, "", run_id="a")
        progress.on_tool_end('[{"url":"https://arxiv.org/abs/1"}]', run_id="a")
        ledger.validate([{"n": 1, "source": "arxiv", "url": "https://arxiv.org/abs/1"}])


if __name__ == "__main__":
    unittest.main()
