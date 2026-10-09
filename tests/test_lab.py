"""Offline behavioral checks: python -m unittest discover -s tests -v."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager

import httpx
from langchain_core.messages import AIMessage

import agents
import research
import tools
from model_limits import ModelTokenPacer, TokenWindow, estimate_input_tokens, retryable_model_error
from check_citations import check, check_citation_coverage, check_structure
from finalize_citations import finalize


def source(n=1, family="web"):
    identifier = f"2501.0000{n}"
    url = (f"https://arxiv.org/abs/{identifier}" if family == "arxiv" else
           f"https://huggingface.co/papers/{identifier}" if family.startswith("hf-") else
           f"https://example.org/paper{n}")
    return {"n": n, "id": identifier, "url": url, "title": f"Paper {n}",
            "date": "2025-01-01", "source": family}


def report(sources, body=None, full_structure=False):
    body = body or "Evidence " + "".join(f"[{s['n']}]" for s in sources)
    if not full_structure:
        return "# Survey\n\n" + body + "\n\n## References\n" + "\n".join(
            f"[{s['n']}] {s['title']}. {s['source']}. {s['url']} ({s['date']})" for s in sources) + "\n"
    return ("# Survey\n\n## TL;DR\n- " + body + "\n\n## Background\n" + body +
            "\n\n## Theme A\n" + body + "\n\n## Theme B\n" + body + "\n\n## Theme C\n" + body +
            "\n\n## Trends and open problems\n" + body + "\n\n## References\n") + "\n".join(
        f"[{s['n']}] {s['title']}. {s['source']}. {s['url']} ({s['date']})" for s in sources) + "\n"


class CitationsTests(unittest.TestCase):
    def test_valid_and_grouped_citations(self):
        sources = [source(n) for n in (1, 2, 3)]
        for body in ("Claim [1][2][3]", "Claim [1, 2, 3]", "Claim [1-3]", "Claim [1–3]"):
            with self.subTest(body=body):
                self.assertEqual(check(report(sources, body), sources), [])

    def test_references_do_not_count_as_body_citations(self):
        self.assertTrue(any("never cited" in p for p in check(report([source()], "No evidence"), [source()])))

    def test_code_and_links_do_not_count(self):
        for body in ("`[1]`", "``[1]``", "```python\n[1]\n```", "~~~\n[1]\n~~~",
                     "    [1]\n", "[1](https://example.org)", "[1][link]"):
            with self.subTest(body=body):
                self.assertTrue(any("never cited" in p for p in check(report([source()], body), [source()])))

    def test_unknown_body_citation(self):
        self.assertTrue(any("[9] cited" in p for p in check(report([source()], "Claim [1][9]"), [source()])))

    def test_wrong_source_family_url_is_rejected_in_sandbox_validator(self):
        entry = source(1, "hf-search")
        entry["source"] = "arxiv"
        self.assertTrue(any("label/URL conflict" in issue for issue in check(report([entry]), [entry])))

    def test_duplicate_urls_and_numbers(self):
        for duplicate in (dict(source(), n=2), source()):
            sources = [source(), duplicate]
            self.assertTrue(any("duplicate" in p for p in check(report(sources), sources)))

    def test_invalid_source_shapes(self):
        for sources in (None, {}, [], [None], [{"n": True, "url": "file:///x"}], [{"n": [], "url": []}]):
            with self.subTest(sources=sources):
                self.assertTrue(check("# Survey", sources))

    def test_missing_heading_or_reference(self):
        self.assertTrue(check("Claim [1]", [source()]))
        self.assertTrue(check("Claim [1]\n## References\n", [source()]))

    def test_reference_mismatch_and_bundling(self):
        valid = report([source()], full_structure=True)
        for altered in (valid.replace("https://example.org/paper1", "https://wrong.org/paper"),
                        valid + "[1] Duplicate. https://example.org/paper1\n",
                        valid.replace(" (2025", "; Second. https://example.org/other (2025"),
                        valid + "[2] Extra. https://example.org/extra\n"):
            self.assertTrue(check(altered, [source()]))

    def test_finalizer_output_and_idempotence(self):
        sources = [source(7), source(2), dict(source(7), n=9), source(10)]
        text, final_sources, issues = finalize("# Survey\nClaims [9][2][7].", sources)
        self.assertEqual(issues, [])
        self.assertEqual(len(final_sources), 2)
        self.assertEqual(check(text, final_sources), [])
        self.assertEqual(finalize(text, final_sources), (text, final_sources, []))

    def test_required_template_sections(self):
        valid = report([source()], full_structure=True)
        self.assertEqual(check_structure(valid), [])
        self.assertTrue(check_structure(valid.replace("## Trends and open problems", "## Open issues")))
        self.assertTrue(check_structure(valid.replace("## Background", "## Background (definition)")))
        self.assertTrue(check_structure(valid.replace("## Theme C\n", "### Theme C\n")))

    def test_uncited_substantial_prose_and_bullets_are_flagged(self):
        claim = "Latent world models predict environmental transitions from compact internal states and support planning over imagined trajectories."
        self.assertTrue(check_citation_coverage("# Survey\n\n" + claim + "\n\n## References\n"))
        self.assertEqual(check_citation_coverage("# Survey\n\n" + claim + " [1]\n\n## References\n"), [])
        self.assertTrue(check_citation_coverage("# Survey\n- Short cited point [1]\n- " + claim))


class RetryAndToolsTests(unittest.TestCase):
    @patch("tools.time.sleep")
    @patch("tools.random.uniform", return_value=0.25)
    def test_backoff_cap_then_success(self, jitter, sleep):
        failures = [tools.RetryableError("busy"), tools.RetryableError("busy"), "ok"]
        from unittest.mock import Mock
        fn = Mock(side_effect=failures)
        self.assertEqual(tools.with_retry(fn, base=2, cap=3), "ok")
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2.25, 3])

    @patch("tools.time.sleep")
    def test_retry_after_and_no_final_sleep(self, sleep):
        def fail():
            raise tools.RetryableError("busy", retry_after=12)
        with self.assertRaises(tools.RetryableError):
            tools.with_retry(fail, attempts=3, cap=10)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [10, 10])

    @patch("tools.time.sleep")
    def test_permanent_errors_never_retry(self, sleep):
        def fail():
            raise ValueError("programming error")
        with self.assertRaises(ValueError):
            tools.with_retry(fail)
        sleep.assert_not_called()

    @patch("tools.httpx.request")
    def test_http_transient_vs_authentication(self, request):
        for status in (429, 500, 502, 503, 504):
            request.return_value = httpx.Response(status, headers={"Retry-After": "7"},
                                                 request=httpx.Request("GET", tools.ARXIV_URL))
            with self.assertRaises(tools.RetryableError) as caught:
                tools._request("GET", tools.ARXIV_URL)
            self.assertEqual(caught.exception.retry_after, 7)
        request.return_value = httpx.Response(401, request=httpx.Request("GET", tools.ARXIV_URL))
        with self.assertRaises(httpx.HTTPStatusError):
            tools._request("GET", tools.ARXIV_URL)
        request.side_effect = httpx.ConnectError("offline")
        with self.assertRaises(tools.RetryableError):
            tools._request("GET", tools.ARXIV_URL)

    @patch("tools._arxiv_request")
    def test_arxiv_query_normalization_and_empty_input(self, request):
        self.assertEqual(tools.arxiv_search.invoke({"query": 'AND OR all:""'}), "NO RESULTS")
        request.assert_not_called()
        request.return_value = SimpleNamespace(text='''<feed xmlns="http://www.w3.org/2005/Atom">
        <entry><id>http://arxiv.org/abs/2501.00001v2</id><title> A\n  Paper </title>
        <published>2025-01-01T12:00:00Z</published><summary> Evidence\n here </summary></entry></feed>''')
        records = json.loads(tools.arxiv_search.invoke({"query": 'all:"world" AND model', "max_results": 100}))
        self.assertEqual(records[0]["url"], "https://arxiv.org/abs/2501.00001")
        self.assertEqual(records[0]["source"], "arxiv")
        self.assertEqual(records[0]["title"], "A Paper")
        self.assertEqual(request.call_args.args[0]["search_query"], "all:world AND all:model")
        self.assertEqual(request.call_args.args[0]["max_results"], 30)

    @patch("tools._request")
    @patch("tools.time.monotonic", side_effect=[1.0, 1.0, 2.0, 4.0])
    @patch("tools.time.sleep")
    def test_arxiv_spacing(self, sleep, monotonic, request):
        with patch.object(tools, "_last_arxiv_call", None):
            tools._arxiv_request({})
            tools._arxiv_request({})
        sleep.assert_called_once_with(2.0)

    @patch("tools._request")
    def test_hf_mapping_sorting_filtering_and_ai_summary(self, request):
        items = [{"paper": {"id": "2501.00001", "title": "World Model", "summary": "long",
                            "ai_summary": "short", "upvotes": 2}},
                 {"paper": {"id": "2501.00002", "title": "World Planning", "upvotes": 5}},
                 {"paper": {"title": "Missing id"}}]
        request.return_value = SimpleNamespace(json=lambda: items)
        daily = json.loads(tools.hf_daily_papers.invoke({"keyword": "world"}))
        self.assertEqual([r["upvotes"] for r in daily], [5, 2])
        self.assertEqual(daily[0]["source"], "hf-daily")
        search = json.loads(tools.hf_search_papers.invoke({"query": "world"}))
        self.assertEqual(search[0]["summary"], "short")
        self.assertEqual(search[0]["source"], "hf-search")
        self.assertEqual(tools.hf_daily_papers.invoke({"keyword": "unrelated"}), "NO RESULTS")

    def test_sse_and_json_payloads(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "evidence"}]}}
        for response in (httpx.Response(200, json=payload),
                         httpx.Response(200, text="event: message\ndata: " + json.dumps(payload) + "\n\n")):
            self.assertEqual(tools._mcp_payload(response), payload)

    @patch("tools.time.sleep")
    @patch("tools._request")
    def test_exa_http200_rate_limit_retries(self, request, sleep):
        request.side_effect = [httpx.Response(200, json={"result": {"_meta": {"rateLimited": True},
                                                "content": [{"type": "text", "text": "busy"}]}}),
                               httpx.Response(200, json={"result": {"content": [{"type": "text", "text": "evidence"}]}})]
        self.assertEqual(tools.web_search.invoke({"query": "world"}), "evidence")
        self.assertEqual(request.call_count, 2)
        sleep.assert_called_once()

    def test_rate_limit_discussion_is_normal_content(self):
        self.assertFalse(tools._rate_limited({}, "This research studies rate limits in LLM services."))
        self.assertTrue(tools._rate_limited({}, "You have hit the rate limit."))

    @patch("tools._request")
    def test_credentials_redacted_and_jsonrpc_errors(self, request):
        fake_key = "offline-test-credential"
        with patch.dict(os.environ, {"EXA_API_KEY": fake_key}):
            request.return_value = httpx.Response(200, json={"error": {"code": -1, "message": fake_key}})
            result = tools.web_search.invoke({"query": "world"})
            self.assertTrue(result.startswith("ERROR:"))
            self.assertNotIn(fake_key, result)
            self.assertIn("[REDACTED]", result)

    @patch("tools._exa_call", return_value="x" * 20000)
    def test_fetch_bounds(self, call):
        self.assertEqual(len(tools.web_fetch.invoke({"url": "https://example.org"})), 12000)
        self.assertEqual(call.call_args.args[1]["urls"], ["https://example.org"])
        self.assertTrue(tools.web_fetch.invoke({"url": "file:///secrets"}).startswith("ERROR:"))

    @patch("tools._request", side_effect=ValueError("broken response"))
    def test_all_tools_return_error_strings(self, request):
        for fn, args in [(tools.arxiv_search, {"query": "world"}),
                         (tools.hf_daily_papers, {}), (tools.hf_search_papers, {"query": "world"}),
                         (tools.web_search, {"query": "world"}),
                         (tools.web_fetch, {"url": "https://example.org"})]:
            with self.subTest(tool=fn.name):
                self.assertTrue(fn.invoke(args).startswith("ERROR:"))


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.sources = [source(1, "arxiv"), source(2, "hf-search"), source(3, "web")]
        self.report = report(self.sources, full_structure=True).encode()
        self.data = json.dumps(self.sources, indent=4).encode()
        self.messages = [AIMessage(content="", tool_calls=[{"name": "task", "args": {}, "id": str(i)}
                                                        for i in range(3)],
                                   usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})]

    def test_slug_path_safety(self):
        for topic in ("../../x", "", "...", "A" * 200, "Survey / World Model", "Tiếng Việt"):
            slug = research.slugify(topic)
            self.assertTrue(slug)
            self.assertLessEqual(len(slug), 60)
            self.assertNotIn("/", slug)
            self.assertNotIn("\\", slug)
            self.assertNotIn("..", slug)
        self.assertEqual(research.slugify("survey about world model"), "survey-about-world-model")

    def test_lead_metadata_only(self):
        metadata = research.summarize(self.messages, 1.27, "test-model")
        self.assertEqual(metadata["subagent_calls"], 3)
        self.assertEqual(metadata["elapsed_s"], 1.3)
        self.assertEqual(metadata["tokens"], {"input": 10, "output": 5})

    @patch("research.download")
    def test_save_preserves_exact_sandbox_bytes(self, download):
        download.return_value = {research.REPORT_PATH: self.report, research.SOURCES_PATH: self.data}
        with tempfile.TemporaryDirectory() as folder:
            path = research.save_outputs(None, "topic", self.messages, 1, "test", folder)
            self.assertEqual(path.read_bytes(), self.report)
            self.assertEqual((Path(folder) / "topic.sources.json").read_bytes(), self.data)
            metadata = json.loads((Path(folder) / "topic.meta.json").read_bytes())
            self.assertEqual(metadata["source_families"], ["arxiv", "hf-search", "web"])

    @patch("research.download")
    def test_invalid_downloads_write_nothing(self, download):
        for report_data, source_data in ((None, self.data), (b"  ", self.data),
                                         (self.report, b"broken"), (self.report, b"{}"),
                                         (self.report, b"[]"), (b"Claim [999]", self.data)):
            download.return_value = {research.REPORT_PATH: report_data, research.SOURCES_PATH: source_data}
            with tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(RuntimeError):
                    research.save_outputs(None, "topic", self.messages, 1, "test", folder)
                self.assertEqual(list(Path(folder).iterdir()), [])

    @patch("research.download")
    def test_failed_run_preserves_previous_reports(self, download):
        download.return_value = {research.REPORT_PATH: b"", research.SOURCES_PATH: self.data}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "topic.md"
            path.write_bytes(b"previous valid report")
            with self.assertRaises(RuntimeError):
                research.save_outputs(None, "topic", self.messages, 1, "test", folder)
            self.assertEqual(path.read_bytes(), b"previous valid report")
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    @patch("research.download")
    def test_missing_delegation_and_source_diversity_rejected(self, download):
        download.return_value = {research.REPORT_PATH: self.report, research.SOURCES_PATH: self.data}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                research.save_outputs(None, "topic", [], 1, "test", folder)
            sources = [source(1)]
            download.return_value = {research.REPORT_PATH: report(sources).encode(),
                                     research.SOURCES_PATH: json.dumps(sources).encode()}
            with self.assertRaises(RuntimeError):
                research.save_outputs(None, "topic", self.messages, 1, "test", folder)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_source_labels_match_urls(self):
        sources = copy.deepcopy(self.sources)
        sources[0]["url"] = "https://example.org/fake"
        with self.assertRaises(RuntimeError):
            research._validate_sources(sources)

    def test_output_replacement_failure_rolls_back(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "topic.md"
            path.write_bytes(b"old")
            replace = os.replace
            def failing_replace(src, dest):
                if str(dest).endswith("topic.sources.json"):
                    raise OSError("disk failure")
                return replace(src, dest)
            with patch("research.os.replace", side_effect=failing_replace), self.assertRaises(OSError):
                research._write_outputs({"topic.md": b"new", "topic.sources.json": b"[]"}, folder)
            self.assertEqual(path.read_bytes(), b"old")
            self.assertEqual(len(list(Path(folder).iterdir())), 1)

    @patch("research.open_sandbox")
    @patch("research.make_model")
    def test_empty_topic_and_placeholder_fail_before_sandbox(self, make_model, sandbox):
        self.assertEqual(research.main(""), 2)
        with patch.dict(os.environ, {"LAB_MODEL": "openai:<model name>"}):
            self.assertEqual(research.main("topic"), 1)
        make_model.assert_not_called()
        sandbox.assert_not_called()

    @patch("research.upload")
    @patch("research.build_lead_agent")
    @patch("research.make_model")
    def test_agent_failure_always_exits_sandbox(self, make_model, build, upload):
        cleaned = []
        @contextmanager
        def box():
            try:
                yield SimpleNamespace(execute=lambda command: SimpleNamespace(exit_code=0, output=""))
            finally:
                cleaned.append(True)
        build.return_value.invoke.side_effect = RuntimeError("model failure")
        with patch.dict(os.environ, {"LAB_MODEL": "test:model"}), patch("research.open_sandbox", box), \
                patch("research.save_outputs") as save:
            self.assertEqual(research.main("topic"), 1)
            save.assert_not_called()
        self.assertEqual(cleaned, [True])
        self.assertEqual(build.return_value.invoke.call_args.kwargs["config"]["recursion_limit"], 1000)

    @patch("research.upload")
    @patch("research.build_lead_agent")
    @patch("research.make_model")
    def test_failed_upload_prevents_agent_run(self, make_model, build, upload):
        from unittest.mock import Mock
        backend = SimpleNamespace(execute=Mock(side_effect=[SimpleNamespace(exit_code=0, output=""),
                                                           SimpleNamespace(exit_code=1, output="missing script")]))
        @contextmanager
        def box():
            yield backend
        with patch.dict(os.environ, {"LAB_MODEL": "test:model"}), patch("research.open_sandbox", box):
            self.assertEqual(research.main("topic"), 1)
        build.assert_not_called()


class AgentTests(unittest.TestCase):
    def test_real_graph_compiles_without_network(self):
        from deepagents.backends import StateBackend
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model="offline-test", api_key="offline-test")
        graph = agents.build_lead_agent(StateBackend(), model)
        self.assertIn("model", graph.nodes)
        self.assertIn("tools", graph.nodes)

    @patch("agents.create_deep_agent")
    def test_every_subagent_has_limits(self, create):
        agents.build_lead_agent(None, None)
        config = create.call_args.kwargs
        for spec in config["subagents"]:
            limits = [m for m in spec["middleware"] if hasattr(m, "run_limit")]
            self.assertEqual(len(limits), 2)
            for middleware in limits:
                self.assertGreater(middleware.run_limit, 0)
            pacer = next(m for m in spec["middleware"] if isinstance(m, ModelTokenPacer))
            self.assertIs(pacer.window, agents.MODEL_WINDOW)
        self.assertEqual({s["name"] for s in agents.build_subagents()}, {"researcher", "citation-checker"})


class ModelPacingTests(unittest.TestCase):
    def fake_time(self):
        clock = SimpleNamespace(now=0.0, sleeps=[])
        def sleep(delay):
            clock.sleeps.append(delay)
            clock.now += delay
        return clock, lambda: clock.now, sleep

    def test_combined_requests_wait_for_window_then_resume(self):
        clock, now, sleep = self.fake_time()
        window = TokenWindow(budget=100, period=60, clock=now, sleep=sleep)
        window.reserve(60)
        window.reserve(40)
        self.assertEqual(clock.sleeps, [])
        window.reserve(30)
        self.assertEqual(clock.sleeps, [60])
        window.reserve(60)
        self.assertEqual(clock.sleeps, [60])

    def test_oversized_request_fails_without_waiting_forever(self):
        clock, now, sleep = self.fake_time()
        window = TokenWindow(budget=100, clock=now, sleep=sleep)
        with self.assertRaises(RuntimeError):
            window.reserve(101)
        self.assertEqual(clock.sleeps, [])

    def test_estimate_includes_system_history_and_tool_schema(self):
        request = SimpleNamespace(system_message=None, messages=[], tools=[])
        baseline = estimate_input_tokens(request)
        request.system_message = "system guidance" * 20
        request.messages = [AIMessage(content="evidence" * 40)]
        request.tools = [tools.web_fetch]
        self.assertGreater(estimate_input_tokens(request), baseline)

    def test_retry_classifier_excludes_auth_billing_and_programming_errors(self):
        for status in (429, 500, 502, 503, 504):
            error = RuntimeError("service failure")
            error.status_code = status
            self.assertTrue(retryable_model_error(error))
        for status in (400, 401, 402, 403):
            error = RuntimeError("permanent failure")
            error.status_code = status
            self.assertFalse(retryable_model_error(error))
        self.assertFalse(retryable_model_error(ValueError("bug")))
        self.assertTrue(retryable_model_error(httpx.ConnectError("temporary")))

    @patch("langchain.agents.middleware.model_retry.time.sleep")
    def test_each_model_retry_reserves_input_budget(self, sleep):
        from langchain.agents.middleware import ModelRetryMiddleware
        from unittest.mock import Mock
        window = Mock()
        pacer = ModelTokenPacer(window)
        retry = ModelRetryMiddleware(max_retries=3, retry_on=retryable_model_error,
                                     initial_delay=15, on_failure="error", jitter=False)
        error = RuntimeError("temporary quota")
        error.status_code = 429
        handler = Mock(side_effect=[error, "success"])
        request = SimpleNamespace(system_message=None, messages=[], tools=[])
        result = retry.wrap_model_call(request, lambda r: pacer.wrap_model_call(r, handler))
        self.assertEqual(result, "success")
        self.assertEqual(window.reserve.call_count, 2)
        sleep.assert_called_once_with(15)

    @patch("langchain.agents.middleware.model_retry.time.sleep")
    def test_retry_exhaustion_propagates(self, sleep):
        from langchain.agents.middleware import ModelRetryMiddleware
        from unittest.mock import Mock
        error = RuntimeError("temporary quota")
        error.status_code = 429
        handler = Mock(side_effect=error)
        retry = ModelRetryMiddleware(max_retries=3, retry_on=retryable_model_error,
                                     initial_delay=15, on_failure="error", jitter=False)
        with self.assertRaises(RuntimeError):
            retry.wrap_model_call(SimpleNamespace(), handler)
        self.assertEqual(handler.call_count, 4)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [15, 30, 60])


class CheckpointTests(unittest.TestCase):
    @patch("research.download")
    def test_failed_evidence_survives_without_entering_reports(self, download):
        note = research.NOTES_DIR + "/01-topic.md"
        outside = "/tmp/work/research/notes/../../outside.md"
        backend = SimpleNamespace(execute=lambda command: SimpleNamespace(
            exit_code=0, output=json.dumps([note, outside])))
        download.return_value = {research.REPORT_PATH: b"unfinished draft",
                                 research.SOURCES_PATH: b"[]", note: b"retrieved evidence"}
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(research.save_checkpoint(backend, "../../topic", folder), 3)
            self.assertNotIn(outside, download.call_args.args[1])
            root = Path(folder) / "topic"
            self.assertEqual((root / "notes/01-topic.md").read_bytes(), b"retrieved evidence")
            self.assertEqual(list(root.glob("*.meta.json")), [])
            self.assertFalse((Path(folder) / "reports").exists())

    @patch("research.upload")
    def test_restore_carries_evidence_without_old_metadata(self, upload):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "topic"
            (root / "notes").mkdir(parents=True)
            (root / "notes/01-topic.md").write_bytes(b"retrieved evidence")
            (root / "draft.report.md").write_bytes(b"unfinished draft")
            (root / "old.meta.json").write_text('{"subagent_calls":999}')
            self.assertTrue(research.restore_checkpoint(None, "topic", folder))
            payload = upload.call_args.args[1]
            self.assertEqual(payload[research.NOTES_DIR + "/01-topic.md"], b"retrieved evidence")
            self.assertFalse(any("meta" in name for name in payload))

    @patch("research.download", return_value={})
    def test_missing_evidence_does_not_create_checkpoint(self, download):
        backend = SimpleNamespace(execute=lambda command: SimpleNamespace(exit_code=0, output="[]"))
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(research.save_checkpoint(backend, "topic", folder), 0)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
