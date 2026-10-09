"""Check setup without invoking an LLM or printing credentials."""
import os
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def main():
    ready = True
    print(f"Python: {sys.version.split()[0]}")
    for name in ("deepagents", "langchain-openai", "langchain-daytona", "daytona", "httpx", "python-dotenv"):
        try:
            print(f"{name}: {version(name)}")
        except PackageNotFoundError:
            ready = False
            print(f"{name}: MISSING")
    name = (os.getenv("LAB_MODEL") or os.getenv("OPENAI_DEPLOYMENT_MODEL") or "").strip()
    configured = bool(name and "<" not in name and ">" not in name)
    ready &= configured
    print(f"LLM model: {'configured' if configured else 'MISSING (set LAB_MODEL in .env)'}")
    # Report presence only, never values. A local compatible server may not need a key.
    base_url = os.getenv("LAB_BASE_URL") or os.getenv("OPENAI_ENDPOINT")
    key_names = (["LAB_API_KEY", "OPENAI_KEY"] if base_url else
                 {"openai": ["OPENAI_API_KEY"], "anthropic": ["ANTHROPIC_API_KEY"],
                  "google_genai": ["GOOGLE_API_KEY", "GEMINI_API_KEY"]}.get(name.split(":")[0], []))
    present = any(os.getenv(key, "").strip() for key in key_names)
    local = bool(base_url and any(host in base_url for host in ("localhost", "127.0.0.1", "[::1]")))
    if key_names:
        print(f"LLM credentials: {'present' if present else 'not required for local server' if local else 'MISSING'}")
        ready &= present or local
    kind = (os.getenv("SANDBOX") or "daytona").lower()
    print(f"Sandbox: {kind}")
    if kind == "docker":
        try:
            result = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}"],
                                    capture_output=True, text=True, timeout=15)
            running = result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            running = False
        ready &= running
        print(f"Docker engine: {'ready' if running else 'not available (start Docker Desktop)'}")
    elif kind == "daytona":
        present = bool(os.getenv("DAYTONA_API_KEY", "").strip())
        ready &= present
        print(f"Daytona credentials: {'present' if present else 'MISSING'}")
    else:
        ready = False
        print("Invalid SANDBOX; use docker or daytona")
    print(f"Exa credentials: {'present' if os.getenv('EXA_API_KEY') else 'absent (free endpoint; rate limits apply)'}")
    print("READY for a real research run" if ready else "NOT READY: complete the missing configuration")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
