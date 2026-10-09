"""Verify cached source discoveries with the real host tools before resuming."""
import argparse
import json
import re

from provenance import SourceLedger
from research import CHECKPOINTS, slugify
from tools import arxiv_search, hf_daily_papers, hf_search_papers, web_search

TOOLS = {"arxiv_search": arxiv_search, "hf_daily_papers": hf_daily_papers,
         "hf_search_papers": hf_search_papers, "web_search": web_search}
FAMILY_TO_TOOL = {"arxiv": "arxiv_search", "hf-search": "hf_search_papers",
                  "hf-daily": "hf_daily_papers", "web": "web_search"}


def plan_for_sources(sources):
    plan = []
    for source in sources:
        name = FAMILY_TO_TOOL[source["source"]]
        if name == "arxiv_search":
            args = {"query": source["title"], "max_results": 30}
        elif name == "hf_search_papers":
            args = {"query": source["title"], "limit": 5}
        elif name == "hf_daily_papers":
            args = {"keyword": source["title"].split(":")[0], "limit": 50}
        else:
            args = {"query": source["url"], "objective": "Find this primary research page and its actual URL", "num_results": 3}
        plan.append((name, args, source.get("id")))
    return plan


INFERENCE_PLAN = [
    ("arxiv_search", {"query": "FlashAttention Fast Memory Efficient Exact Attention IO Awareness", "max_results": 15}, None),
    ("arxiv_search", {"query": "Efficient Memory Management Large Language Model Serving PagedAttention", "max_results": 15}, None),
    ("hf_search_papers", {"query": "AWQ Activation-aware Weight Quantization", "limit": 3}, None),
    ("hf_search_papers", {"query": "GPTQ Accurate Post-Training Quantization", "limit": 3}, None),
    ("hf_search_papers", {"query": "Fast Inference from Transformers via Speculative Decoding", "limit": 3}, None),
    ("hf_search_papers", {"query": "TinyLlama An Open-Source Small Language Model", "limit": 3}, None),
    ("hf_search_papers", {"query": "DistilBERT", "limit": 3}, None),
    ("hf_daily_papers", {"keyword": "inference", "limit": 50}, None),
    ("web_search", {"query": "vLLM PagedAttention efficient inference official documentation", "num_results": 3}, None),
]


def evidence_notes(name, result, identifier=None):
    """Copy retrieved metadata/excerpts; never synthesize paper claims on host."""
    if result.startswith("ERROR:") or result == "NO RESULTS":
        return ""
    if name == "web_search":
        chunks = re.split(r"\n\s*---+\s*\n", result)
        return "\n\n".join("## Raw web discovery (source: web)\n" + chunk[:1800] for chunk in chunks[:3])
    records = json.loads(result)
    selected = [r for r in records if r.get("id") == identifier] if identifier else []
    selected = selected or records[:3]
    blocks = []
    for item in selected:
        family = {"arxiv_search": "arxiv", "hf_search_papers": "hf-search", "hf_daily_papers": "hf-daily"}[name]
        blocks.append(f"## {item['title']}\n- id: {item['id']}\n- url: {item['url']}\n"
                      f"- date: {item.get('published') or 'n.d.'}\n- source: {family}\n"
                      "### Evidence\n- Retrieved excerpt (abstract/summary only): " + item.get("summary", "") +
                      "\n### Limitations\n- Verify detailed claims against primary text; HF AI summaries may be inaccurate.")
    return "\n\n".join(blocks)


def main(topic):
    folder = CHECKPOINTS / slugify(topic)
    draft = folder / "draft.sources.json"
    if draft.exists():
        plan = plan_for_sources(json.loads(draft.read_bytes()))
    elif "efficient inference" in topic:
        plan = INFERENCE_PLAN
    else:
        raise ValueError("no cached manifest or preset source plan for this topic")
    ledger = SourceLedger()
    receipts, notes = [], []
    for index, (name, args, identifier) in enumerate(plan, 1):
        print(f"[{index}/{len(plan)}] Verify discovery via {name}", flush=True)
        result = TOOLS[name].invoke(args)
        ledger.record(name, result)
        receipts.append({"tool": name, "arguments": args, "result": result})
        notes.append(evidence_notes(name, result, identifier))
        if result.startswith("ERROR:") or result == "NO RESULTS":
            print(result[:200], flush=True)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "verified_discoveries.json").write_text(json.dumps(ledger.records(), indent=2), encoding="utf-8")
    (folder / "source_receipts.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    (folder / "notes").mkdir(exist_ok=True)
    (folder / "notes/90-verified-source-results.md").write_text("\n\n".join(filter(None, notes)), encoding="utf-8")
    print(f"Verified {len(ledger.records())} source-label/URL pairs; no model calls or reports written.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic")
    raise SystemExit(main(parser.parse_args().topic))
