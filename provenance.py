"""Host-side discovery evidence that an agent cannot rewrite in its sandbox."""
import json
import re
import threading

DISCOVERY_TOOLS = {"arxiv_search": "arxiv", "hf_daily_papers": "hf-daily",
                   "hf_search_papers": "hf-search", "web_search": "web"}


class SourceLedger:
    def __init__(self, records=None):
        self._lock = threading.Lock()
        self._seen = set()
        # Only the host runner supplies previously recorded discovery metadata.
        for record in records or []:
            if (not isinstance(record, dict) or record.get("source") not in DISCOVERY_TOOLS.values()
                    or not isinstance(record.get("url"), str) or not record["url"].startswith(("https://", "http://"))):
                raise ValueError("invalid historical discovery record")
            self._seen.add((record["source"], record["url"]))

    def record(self, tool_name, content):
        family = DISCOVERY_TOOLS.get(tool_name)
        if not family or not isinstance(content, str) or content.startswith("ERROR:") or content == "NO RESULTS":
            return
        if family == "web":
            urls = [url.rstrip(".,;!?)]}") for url in re.findall(r'https?://[^\s<>"\x27`]+', content)]
        else:
            try:
                records = json.loads(content)
            except ValueError:
                return
            urls = [item["url"] for item in records if isinstance(item, dict) and isinstance(item.get("url"), str)] if isinstance(records, list) else []
        with self._lock:
            self._seen.update((family, url) for url in urls)

    def validate(self, sources):
        with self._lock:
            missing = [f"[{item['n']}] {item['source']} {item['url']}" for item in sources
                       if (item["source"], item["url"]) not in self._seen]
        if missing:
            raise RuntimeError("sources were not returned by their claimed discovery tools in this run: " + "; ".join(missing))

    def records(self):
        with self._lock:
            return [{"source": family, "url": url} for family, url in sorted(self._seen)]
