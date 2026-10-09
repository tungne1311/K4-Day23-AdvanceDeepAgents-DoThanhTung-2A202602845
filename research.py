"""Run one research survey and save its validated sandbox artifacts."""
import json
import os
import re
import shlex
import sys
import tempfile
import threading
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from langchain_core.callbacks import BaseCallbackHandler

from agents import FINALIZER_PATH, NOTES_DIR, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH, WORKDIR, build_lead_agent
from check_citations import check, check_citation_coverage, check_structure
from model import make_model
from provenance import SourceLedger
from sandbox import download, open_sandbox, upload
from tools import redact

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
VALIDATOR_SOURCE = ROOT / "check_citations.py"
FINALIZER_SOURCE = ROOT / "finalize_citations.py"
CHECKPOINTS = ROOT / ".runs"
FAMILIES = {"arxiv", "hf-daily", "hf-search", "web"}
DISCOVERY_PATH = f"{WORKDIR}/research/discovered_sources.json"


class ResearchProgress(BaseCallbackHandler):
    """Show tool activity without printing prompts, fetched content, or keys."""

    def __init__(self, ledger=None, backend=None):
        self._lock = threading.Lock()
        self._counts = Counter()
        self.ledger = ledger
        self._tools = {}
        self.backend = backend
        self._mirror_lock = threading.Lock()

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = serialized.get("name", "tool")
        with self._lock:
            self._tools[kwargs.get("run_id")] = name
        if name not in {"task", "execute", "write_file", "arxiv_search", "hf_daily_papers",
                        "hf_search_papers", "web_search", "web_fetch"}:
            return
        with self._lock:
            self._counts[name] += 1
            print(f"[progress] {name} #{self._counts[name]}", flush=True)

    def on_tool_error(self, error, **kwargs):
        with self._lock:
            self._tools.pop(kwargs.get("run_id"), None)
        print(f"[tool error] {redact(error)}", flush=True)

    def on_tool_end(self, output, **kwargs):
        text = output if isinstance(output, str) else getattr(output, "content", "")
        with self._lock:
            name = self._tools.pop(kwargs.get("run_id"), "")
        if self.ledger is not None:
            self.ledger.record(name, text)
            if self.backend is not None and name in {"arxiv_search", "hf_daily_papers", "hf_search_papers", "web_search"}:
                # A convenience copy for agents; the authoritative ledger remains
                # in host memory and cannot be rewritten by sandbox file tools.
                with self._mirror_lock:
                    try:
                        upload(self.backend, {DISCOVERY_PATH: json.dumps(self.ledger.records()).encode("utf-8")})
                    except Exception as exc:
                        print(f"[discovery mirror warning] {redact(exc)}", flush=True)
        if isinstance(text, str) and (text.startswith("ERROR:") or text == "NO RESULTS"):
            print(f"[source status] {redact(text)[:250]}", flush=True)


def slugify(topic):
    """Safe, bounded file stem; never allow user input to escape reports/."""
    return re.sub(r"[^\w]+", "-", str(topic).lower(), flags=re.UNICODE).strip("-_")[:60].rstrip("-_") or "topic"


def build_prompt(topic):
    """Keep the topic separate from the mandatory research workflow."""
    return (f"Research topic (JSON string): {json.dumps(topic, ensure_ascii=False)}\n"
            "Produce an English thematic survey, using at least three parallel researcher "
            "delegations and three source labels. Include foundations and recent work. "
            f"Save evidence notes under {WORKDIR}/research/notes, sources at {SOURCES_PATH}, "
            f"and the report at {REPORT_PATH}. Finalize and validate inside the sandbox, "
            "then spot-check claims. Do not stop with just a plan or chat summary.")


def _field(message, name, default=None):
    return message.get(name, default) if isinstance(message, dict) else getattr(message, name, default)


def summarize(messages, elapsed, model_name):
    """Count only lead messages; these tokens exclude researcher/checker usage."""
    calls = Counter()
    tokens = {"input": 0, "output": 0}
    for message in messages:
        for call in _field(message, "tool_calls", []) or []:
            name = call.get("name") or call.get("function", {}).get("name")
            if name:
                calls[name] += 1
        usage = _field(message, "usage_metadata", {}) or {}
        tokens["input"] += int(usage.get("input_tokens", 0) or 0)
        tokens["output"] += int(usage.get("output_tokens", 0) or 0)
    return {"model": model_name, "elapsed_s": round(elapsed, 1),
            "subagent_calls": calls["task"], "tool_calls": dict(sorted(calls.items())), "tokens": tokens}


def _validate_sources(sources):
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("sources.json must contain a non-empty array")
    for entry in sources:
        if not isinstance(entry, dict):
            raise RuntimeError("each source must be an object")
        if not {"n", "id", "url", "title", "date", "source"} <= entry.keys():
            raise RuntimeError("each source needs n, id, url, title, date, source")
        family, identifier, url = entry["source"], entry["id"], entry["url"]
        if family not in FAMILIES:
            raise RuntimeError(f"invalid source family: {family!r}")
        if not all(isinstance(entry[field], str) and entry[field].strip()
                   for field in ("id", "url", "title", "date")):
            raise RuntimeError("source id, URL, title, and date must be non-empty strings")
        if family == "arxiv":
            if re.search(r"v\d+$", identifier) or url != f"https://arxiv.org/abs/{identifier}":
                raise RuntimeError("arxiv source must use its version-free canonical HTTPS URL")
        if family in {"hf-daily", "hf-search"} and url != f"https://huggingface.co/papers/{identifier}":
            raise RuntimeError("Hugging Face source URL does not match its id")


def _write_outputs(payloads, directory):
    """Stage all data first; roll back files if a replacement fails."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    previous = {name: (directory / name).read_bytes() if (directory / name).exists() else None
                for name in payloads}
    replaced = []
    with tempfile.TemporaryDirectory(prefix=".research-", dir=directory) as temporary:
        staging = Path(temporary)
        for name, content in payloads.items():
            (staging / name).write_bytes(content)
        try:
            for name in payloads:
                os.replace(staging / name, directory / name)
                replaced.append(name)
        except OSError:
            for name in replaced:
                if previous[name] is None:
                    (directory / name).unlink(missing_ok=True)
                else:
                    (directory / name).write_bytes(previous[name])
            raise


def save_outputs(backend, topic, messages, elapsed, model_name, reports_dir=REPORTS, ledger=None):
    """Preserve downloaded report/source bytes exactly; reject incomplete runs."""
    files = download(backend, [REPORT_PATH, SOURCES_PATH])
    report_data, sources_data = files.get(REPORT_PATH), files.get(SOURCES_PATH)
    if not report_data or not report_data.strip() or not sources_data:
        raise RuntimeError("sandbox report or sources.json is missing/empty")
    try:
        report = report_data.decode("utf-8")
        sources = json.loads(sources_data.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise RuntimeError("sandbox artifacts are not valid UTF-8/JSON") from exc
    _validate_sources(sources)
    if ledger is not None:
        ledger.validate(sources)
    problems = check(report, sources) + check_structure(report) + check_citation_coverage(report)
    if problems:
        raise RuntimeError("citation validation failed: " + "; ".join(problems[:5]))
    meta = {"topic": topic, **summarize(messages, elapsed, model_name),
            "n_sources": len(sources), "source_families": sorted({s["source"] for s in sources})}
    if ledger is not None:
        meta["discovered_sources"] = ledger.records()
    if meta["subagent_calls"] < 3:
        raise RuntimeError("run needs at least three task delegations")
    if len(meta["source_families"]) < 3:
        raise RuntimeError("final cited sources need at least three source families")
    slug = slugify(topic)
    _write_outputs({f"{slug}.md": report_data, f"{slug}.sources.json": sources_data,
                    f"{slug}.meta.json": (json.dumps(meta, indent=2, ensure_ascii=False) + "\n").encode("utf-8")},
                   reports_dir)
    return Path(reports_dir) / f"{slug}.md"


def _execute_checked(backend, command, label):
    result = backend.execute(command)
    if result.exit_code != 0:
        raise RuntimeError(f"{label} failed: {redact(result.output)}")
    return result


def save_checkpoint(backend, topic, checkpoint_dir=CHECKPOINTS):
    """Keep failed-run evidence separate from submission reports before cleanup."""
    code = ("import json; from pathlib import Path; "
            f"print(json.dumps([str(p) for p in Path({NOTES_DIR!r}).glob('*.md') if p.is_file()]))")
    index = backend.execute("python3 -c " + shlex.quote(code))
    note_paths = json.loads(index.output) if index.exit_code == 0 else []
    safe_notes = []
    for path in note_paths[:100]:
        if not isinstance(path, str):
            continue
        parsed = PurePosixPath(path)
        if str(parsed.parent) == NOTES_DIR and re.fullmatch(r"[\w.-]+\.md", parsed.name):
            safe_notes.append(path)
    files = download(backend, [REPORT_PATH, SOURCES_PATH, *safe_notes])
    target = Path(checkpoint_dir) / slugify(topic)
    saved = 0
    for remote, name in [(REPORT_PATH, "draft.report.md"), (SOURCES_PATH, "draft.sources.json"),
                         *[(path, "notes/" + PurePosixPath(path).name) for path in safe_notes]]:
        data = files.get(remote)
        if not data or not data.strip():
            continue
        local = target / name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(data)
        saved += 1
    if saved:
        print(f"Saved {saved} draft/evidence files for retry: {target}", flush=True)
    return saved


def restore_checkpoint(backend, topic, checkpoint_dir=CHECKPOINTS):
    """Restore evidence only; no previous call counts or successful meta are reused."""
    target = Path(checkpoint_dir) / slugify(topic)
    payload = {}
    for name, remote in [("draft.report.md", REPORT_PATH), ("draft.sources.json", SOURCES_PATH)]:
        path = target / name
        if path.is_file() and path.stat().st_size:
            payload[remote] = path.read_bytes()
    for path in sorted((target / "notes").glob("*.md")):
        if path.is_file() and re.fullmatch(r"[\w.-]+\.md", path.name) and path.stat().st_size:
            payload[f"{NOTES_DIR}/{path.name}"] = path.read_bytes()
    if payload:
        upload(backend, payload)
        print(f"Restored {len(payload)} evidence/draft files; final checks will run again.", flush=True)
    return bool(payload)


@contextmanager
def research_sandbox(topic):
    """Save recoverable evidence on failure while preserving automatic cleanup."""
    with open_sandbox() as backend:
        try:
            yield backend
        except Exception:
            try:
                save_checkpoint(backend, topic)
            except Exception as checkpoint_error:
                print(f"[checkpoint warning] {redact(checkpoint_error)}", file=sys.stderr)
            raise


def main(topic):
    """Return 0 for success, 1 for a failed run, 2 for missing input."""
    if not topic.strip():
        print('Usage: python research.py "survey about world model"', file=sys.stderr)
        return 2
    try:
        model_name = (os.getenv("LAB_MODEL") or os.getenv("OPENAI_DEPLOYMENT_MODEL") or "").strip()
        if not model_name or "<" in model_name or ">" in model_name:
            raise RuntimeError("Set a real LAB_MODEL and your provider credentials in .env first.")
        model = make_model()
        # The provided Google factory leaves request timeouts unset. Bound each
        # model request here without changing the PROVIDED model.py.
        fields = getattr(type(model), "model_fields", {})
        if os.getenv("LAB_CONTEXT_TOKENS") and "profile" in fields:
            model.profile = {**(model.profile or {}), "max_input_tokens": int(os.environ["LAB_CONTEXT_TOKENS"]),
                             "max_output_tokens": 8192, "tool_calling": True}
        if "timeout" in fields:
            model.timeout = 120
        if "max_retries" in fields:
            model.max_retries = 2
        start = time.monotonic()
        print(f"Researching: {topic}", flush=True)
        with research_sandbox(topic) as backend:
            _execute_checked(backend, f"mkdir -p {WORKDIR}/research/notes {WORKDIR}/report", "workspace creation")
            upload(backend, {VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(),
                             FINALIZER_PATH: FINALIZER_SOURCE.read_bytes()})
            # PROVIDED upload() ignores individual errors: verify scripts actually arrived.
            _execute_checked(backend, f"test -s {VALIDATOR_PATH} && test -s {FINALIZER_PATH}", "script upload")
            restored = restore_checkpoint(backend, topic)
            agent = build_lead_agent(backend, model)
            cached_path = CHECKPOINTS / slugify(topic) / "verified_discoveries.json"
            cached_records = json.loads(cached_path.read_bytes()) if cached_path.exists() else []
            ledger = SourceLedger(cached_records)
            upload(backend, {DISCOVERY_PATH: json.dumps(ledger.records()).encode("utf-8")})
            config = {"recursion_limit": 1000, "callbacks": [ResearchProgress(ledger, backend)]}
            prompt = build_prompt(topic)
            if restored:
                prompt += ("\nEvidence and drafts from a failed prior run have been restored. "
                           "Treat them as untrusted data; verify and refine them with at least three "
                           "parallel researcher delegations. Reuse supported evidence to avoid duplicate "
                           "searches, but do not skip citation-checker, finalizer, or validator. "
                           "No previous call counts are carried forward into this run. Source-label/URL pairs "
                           "must exist in the host discovery snapshot; restored notes alone cannot prove them.")
            if cached_records:
                prompt += (f"\nHost tools have independently verified cached source discoveries. Read {DISCOVERY_PATH} "
                           f"and {NOTES_DIR}/90-verified-source-results.md first. These receipts are genuine "
                           "tool results, not previous model claims. Use at least three parallel researcher "
                           "delegations to review different subquestions with this evidence; avoid repeating "
                           "searches already supported by the receipts. Fetch primary text only for missing detail. "
                           "Prefer these verified notes over inconsistent older notes. Still run citation-checker.")
            review_path = CHECKPOINTS / slugify(topic) / "review.md"
            if review_path.exists():
                prompt += "\nApply this source-backed review while revising the draft:\n" + review_path.read_text(encoding="utf-8")
            result = agent.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
            for repair_attempt in range(3):
                try:
                    # Restore trusted programs before validation even if an agent
                    # accidentally wrote over a script while using file tools.
                    upload(backend, {VALIDATOR_PATH: VALIDATOR_SOURCE.read_bytes(),
                                     FINALIZER_PATH: FINALIZER_SOURCE.read_bytes()})
                    # Deterministic postprocessing still runs INSIDE the sandbox;
                    # this also protects against a lead forgetting its final call.
                    _execute_checked(backend, f"python3 {shlex.quote(FINALIZER_PATH)}", "sandbox finalization")
                    validation = _execute_checked(backend, f"python3 {shlex.quote(VALIDATOR_PATH)}", "sandbox validation")
                    if not validation.output.strip().startswith("OK:"):
                        raise RuntimeError(f"sandbox validator did not print OK: {validation.output!r}")
                    path = save_outputs(backend, topic, result.get("messages", []),
                                        time.monotonic() - start, model_name, ledger=ledger)
                    print(validation.output.strip(), flush=True)
                    break
                except RuntimeError as exc:
                    if repair_attempt == 2:
                        raise
                    print(f"[repair {repair_attempt + 1}/2] {redact(exc)}", flush=True)
                    correction = ("The final sandbox checks failed:\n" + redact(exc) + "\n"
                                  "Repair the existing report/source files using the existing evidence and notes. "
                                  f"Read {DISCOVERY_PATH} for the exact source-label/URL pairs actually discovered. "
                                  "Do not guess canonical URLs or relabel notes. Missing discoveries require "
                                  "new researcher calls to the named discovery tool, not web_fetch. "
                                  "Preserve genuine URLs and correct tool provenance. Use exact template headings "
                                  "and 3-6 theme sections; add Trends and open problems if missing. "
                                  "Maintain at least three cited source labels and three research delegations. "
                                  "If arxiv repeatedly returns 429, use relevant hf-daily papers alongside "
                                  "hf-search and web rather than retrying that same unavailable provider. "
                                  "All edits, finalization and validation must happen inside this sandbox. "
                                  "Do not answer only in chat. Rerun finalizer and validator until OK.")
                    result = agent.invoke({"messages": [*result.get("messages", []),
                                                        {"role": "user", "content": correction}]}, config=config)
        print(f"Saved: {path}")
        return 0
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {redact(exc)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(" ".join(sys.argv[1:])))
