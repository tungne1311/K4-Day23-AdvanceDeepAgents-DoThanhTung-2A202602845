import unittest

from provenance import SourceLedger
from revise_report import merge_metadata


class RevisionTests(unittest.TestCase):
    def test_reuses_genuine_historical_discoveries(self):
        ledger = SourceLedger([{"source": "hf-search", "url": "https://huggingface.co/papers/1"}])
        ledger.validate([{"n": 1, "source": "hf-search", "url": "https://huggingface.co/papers/1"}])

    def test_rejects_malformed_historical_records(self):
        with self.assertRaises(ValueError):
            SourceLedger([{"source": "invented", "url": "https://example.org"}])

    def test_revision_adds_actual_usage_without_inventing_delegations(self):
        previous = {"elapsed_s": 100, "subagent_calls": 4, "tool_calls": {"task": 4, "execute": 6},
                    "tokens": {"input": 500, "output": 100}}
        stats = {"model": "model", "elapsed_s": 25, "subagent_calls": 0,
                 "tool_calls": {"web_fetch": 1, "execute": 2}, "tokens": {"input": 150, "output": 40}}
        merged = merge_metadata(previous, stats, "correct source claim", "abc")
        self.assertEqual(merged["subagent_calls"], 4)
        self.assertEqual(merged["tool_calls"]["execute"], 8)
        self.assertEqual(merged["tokens"], {"input": 650, "output": 140})
        self.assertEqual(merged["elapsed_s"], 125)
        self.assertEqual(merged["revisions"][0]["before_report_sha256"], "abc")
        self.assertNotIn("revisions", previous)

    def test_repeated_revision_keeps_history(self):
        previous = {"elapsed_s": 100, "subagent_calls": 4, "tool_calls": {"task": 4},
                    "tokens": {"input": 500, "output": 100}, "revisions": [{"review": "first"}]}
        stats = {"elapsed_s": 5, "subagent_calls": 0, "tool_calls": {}, "tokens": {"input": 10, "output": 2}}
        merged = merge_metadata(previous, stats, "second", "hash")
        self.assertEqual(len(merged["revisions"]), 2)
        self.assertEqual(len(previous["revisions"]), 1)


if __name__ == "__main__":
    unittest.main()
