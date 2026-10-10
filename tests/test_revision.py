import unittest
from unittest.mock import Mock, patch

from provenance import SourceLedger
from revise_report import build_focused_agent, merge_metadata
from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH


class RevisionTests(unittest.TestCase):
    @patch("revise_report.create_agent")
    @patch("revise_report.upload")
    def test_focused_submission_runs_checks_inside_sandbox_and_preserves_manifest(self, upload, create):
        backend = Mock()
        backend.execute.side_effect = [Mock(exit_code=0, output="finalized"),
                                       Mock(exit_code=0, output="OK: 1 sources, all citations resolve")]
        trusted = {FINALIZER_PATH: b"trusted finalizer", VALIDATOR_PATH: b"trusted validator"}
        _, state = build_focused_agent(backend, Mock(), b"original report", b"original sources", trusted)
        tools = {item.name: item for item in create.call_args.kwargs["tools"]}
        self.assertEqual(set(tools), {"web_fetch", "save_revision"})
        result = tools["save_revision"].invoke({"report_body": "LLM corrected report"})
        self.assertTrue(state["ok"])
        self.assertTrue(result.startswith("OK:"))
        payload = upload.call_args.args[1]
        self.assertEqual(payload[REPORT_PATH], b"LLM corrected report")
        self.assertEqual(payload[SOURCES_PATH], b"original sources")
        self.assertEqual(payload[VALIDATOR_PATH], trusted[VALIDATOR_PATH])
        self.assertEqual(backend.execute.call_count, 2)

    @patch("revise_report.create_agent")
    @patch("revise_report.upload")
    def test_focused_submission_never_accepts_failed_sandbox_validation(self, upload, create):
        backend = Mock()
        backend.execute.side_effect = [Mock(exit_code=0, output="finalized"),
                                       Mock(exit_code=1, output="unknown citation [8]")]
        _, state = build_focused_agent(backend, Mock(), b"original", b"manifest", {})
        submit = create.call_args.kwargs["tools"][1]
        result = submit.invoke({"report_body": "bad report"})
        self.assertFalse(state["ok"])
        self.assertIn("REJECTED", result)

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
