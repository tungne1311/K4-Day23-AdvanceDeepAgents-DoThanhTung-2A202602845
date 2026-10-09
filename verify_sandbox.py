"""Exercise real sandbox I/O and citation scripts, without LLM calls or reports/."""
import json
from pathlib import Path

from agents import FINALIZER_PATH, REPORT_PATH, SOURCES_PATH, VALIDATOR_PATH
from sandbox import download, open_sandbox, upload
from tools import redact

ROOT = Path(__file__).resolve().parent


def main():
    # Synthetic fixtures exist only inside a disposable sandbox, never in reports/.
    sources = [{"n": 7, "id": "test", "url": "https://example.org/sandbox-test",
                "title": "Sandbox test fixture", "date": "n.d.", "source": "web"}]
    sandbox_id = None
    try:
        with open_sandbox() as backend:
            sandbox_id = backend.id
            upload(backend, {
                VALIDATOR_PATH: (ROOT / "check_citations.py").read_bytes(),
                FINALIZER_PATH: (ROOT / "finalize_citations.py").read_bytes(),
                REPORT_PATH: ("# Sandbox I/O test\n\n## TL;DR\n- Test fixture [7].\n\n"
                              "## Background\nTest [7].\n\n## Theme A\nTest [7].\n\n"
                              "## Theme B\nTest [7].\n\n## Theme C\nTest [7].\n\n"
                              "## Trends and open problems\nTest [7].\n").encode(),
                SOURCES_PATH: json.dumps(sources).encode(),
            })
            for script in (FINALIZER_PATH, VALIDATOR_PATH):
                result = backend.execute(f"python3 {script}")
                if result.exit_code:
                    raise RuntimeError(f"script failed: {result.output}")
                print(result.output.strip())
            downloaded = download(backend, [REPORT_PATH, SOURCES_PATH])
            if not all(downloaded.values()):
                raise RuntimeError("sandbox download failed")
            if b"## References" not in downloaded[REPORT_PATH]:
                raise RuntimeError("finalized References missing")
            if json.loads(downloaded[SOURCES_PATH])[0]["n"] != 1:
                raise RuntimeError("citation renumbering failed")
            print(f"Sandbox upload / execute / download: OK ({sandbox_id})")
        print("Sandbox context exited; automatic cleanup completed.")
        return 0
    except Exception as exc:
        print(f"FAILED: {redact(exc)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
