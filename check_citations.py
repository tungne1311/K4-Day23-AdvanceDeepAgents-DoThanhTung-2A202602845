"""check_citations.py - STUDENT IMPLEMENTS `check`.   Runs INSIDE the sandbox (standard library only).

research.py uploads this file to the sandbox and the lead agent runs it with the `execute` tool:
    python3 /tmp/work/research/check_citations.py [report.md] [sources.json]
It must exit 0 and print "OK: ..." when the report is consistent, else print each problem and exit 1.
"""
import json
import re
import sys
from collections import Counter

REPORT = "/tmp/work/report/report.md"
SOURCES = "/tmp/work/research/sources.json"


def check(report_text, sources):
    """Return a list of problem strings (empty list = OK).

    PSEUDO-CODE:
      problems = []
      if sources is empty: return ["no sources in sources.json"]
      for each source entry:
          n must be an int                       -> problem if not
          url must start with http:// or https://-> problem if not
          the same url must not appear twice     -> problem if duplicated
      split report_text at the heading "## References":
          body = text before it; if the heading is missing -> problem
      cited = set of numbers found as [n] in the BODY only (not in the reference list; use a regex)
      every number in `cited` must exist in sources -> problem "[n] cited but missing from sources.json"
      every source number must be in `cited`        -> problem "source [n] never cited"
      the lines of the References section that start with "[n]" (regex) are the reference lines:
          every source needs exactly ONE reference line (none missing, no number twice, no number that is not a source)
          each reference line holds exactly ONE http(s) URL and it must equal that source's url
          (a line bundling several sources under one number is a problem)
      return problems
    """
    problems = []
    if not isinstance(sources, list) or not sources:
        return ["sources.json must be a non-empty list of sources"]
    by_n, seen_urls = {}, set()
    for index, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            problems.append(f"source entry {index} must be an object")
            continue
        n, url = source.get("n"), source.get("url")
        if type(n) is not int or n < 1:
            problems.append(f"source entry {index}: n must be a positive integer")
        elif n in by_n:
            problems.append(f"duplicate source number [{n}]")
        else:
            by_n[n] = source
        if not isinstance(url, str) or not re.fullmatch(r"https?://\S+", url):
            problems.append(f"source entry {index}: invalid HTTP(S) URL")
        elif url in seen_urls:
            problems.append(f"duplicate source URL: {url}")
        else:
            seen_urls.add(url)
        # Validate provenance when the lab's full source schema is supplied.
        # Running this INSIDE the sandbox lets the lead repair mistakes before
        # downloading; host-only rejection would discard a whole research run.
        family, identifier = source.get("source"), source.get("id")
        if family is not None:
            if not isinstance(family, str) or family not in {"arxiv", "hf-daily", "hf-search", "web"}:
                problems.append(f"source [{n}] has an invalid source family")
            elif family in {"arxiv", "hf-daily", "hf-search"}:
                expected = (f"https://arxiv.org/abs/{identifier}" if family == "arxiv" else
                            f"https://huggingface.co/papers/{identifier}")
                if not isinstance(identifier, str) or not identifier or url != expected:
                    problems.append(f"source [{n}]: {family} label/URL conflict; preserve the discovered URL "
                                    "and recover the correct tool provenance from researcher notes")
                elif family == "arxiv" and re.search(r"v\d+$", identifier):
                    problems.append(f"source [{n}]: arxiv id must omit the version suffix")

    # Code examples and Markdown links are not evidence citations.
    clean = _without_code(report_text)
    headings = list(re.finditer(r"(?m)^##[ \t]+References[ \t]*\r?$", clean))
    if not headings:
        return problems + ["missing ## References heading"]
    if len(headings) != 1:
        problems.append("expected exactly one ## References heading")
    body, references = clean[:headings[0].start()], clean[headings[0].end():]
    body = re.sub(r"\[[^\]\n]*\]\([^\n]*?\)", "", body)
    # Adjacent numeric brackets [1][2] are citations, not reference links.
    body = re.sub(r"\[[^\]\n]*\]\[(?!\d+(?:\s*[,–-]\s*\d+)*\])[^\]\n]*\]", "", body)
    body = re.sub(r"(?m)^\s*\[\d+\]:.*$", "", body)
    cited = set()
    for match in re.finditer(r"(?<!\\)\[(\d+(?:\s*[,–-]\s*\d+)*)\]", body):
        for part in re.split(r"\s*,\s*", match.group(1)):
            span = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", part)
            if span:
                start, end = map(int, span.groups())
                if not 0 <= end - start <= 200:
                    problems.append(f"invalid citation range [{part}]")
                    continue
                cited.update(range(start, end + 1))
            else:
                cited.add(int(part))
    for n in sorted(cited - by_n.keys()):
        problems.append(f"[{n}] cited but missing from sources.json")
    for n in sorted(by_n.keys() - cited):
        problems.append(f"source [{n}] never cited in the body")

    counts = Counter()
    for line in references.splitlines():
        match = re.match(r"^\[(\d+)\]\s*(.*)$", line)
        if not match:
            continue
        n = int(match.group(1))
        counts[n] += 1
        if n not in by_n:
            problems.append(f"reference [{n}] is not a source")
        urls = re.findall(r"https?://[^\s<>]+", match.group(2))
        if len(urls) != 1:
            problems.append(f"reference [{n}] must contain exactly one URL")
        elif n in by_n:
            url = urls[0].rstrip(".,;")
            while url.endswith(")") and url.count(")") > url.count("("):
                url = url[:-1]
            if url != by_n[n].get("url"):
                problems.append(f"reference [{n}] URL differs from sources.json")
    for n in sorted(by_n):
        if counts[n] != 1:
            problems.append(f"source [{n}] needs exactly one reference line (found {counts[n]})")
    return problems


def _without_code(text):
    """Remove fenced/indented code and inline code without changing other lines."""
    lines, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            lines.append("\n")
        elif marker:
            fence = marker[1]
            lines.append("\n")
        elif line.startswith(("    ", "\t")):
            lines.append("\n")
        else:
            lines.append(line)
    return re.sub(r"(`+).*?\1", "", "".join(lines), flags=re.DOTALL)


def check_structure(report_text):
    """Require the English template's headings and three to six thematic sections."""
    clean = _without_code(report_text)
    headings = re.findall(r"(?m)^##[ \t]+(.+?)[ \t]*\r?$", clean)
    required = ["TL;DR", "Background", "Trends and open problems", "References"]
    problems = []
    if not re.search(r"(?m)^# [^\n]+", clean):
        problems.append("missing report title")
    for name in required:
        if headings.count(name) != 1:
            problems.append(f"report needs exactly one literal ## {name} heading")
    if all(headings.count(name) == 1 for name in required):
        positions = [headings.index(name) for name in required]
        if positions != sorted(positions) or positions[:2] != [0, 1] or positions[-1] != len(headings) - 1:
            problems.append("section order must be TL;DR, Background, themes, Trends and open problems, References")
        themes = headings[positions[1] + 1:positions[2]]
        if not 3 <= len(themes) <= 6:
            problems.append(f"report needs 3-6 thematic sections (found {len(themes)})")
    return problems


def check_citation_coverage(report_text):
    """Flag substantial uncited prose/bullets; semantic support still needs checking."""
    body = re.split(r"(?m)^##[ \t]+References[ \t]*\r?$", _without_code(report_text), maxsplit=1)[0]
    blocks, current = [], []
    for line in body.splitlines():
        if not line.strip() or line.startswith("#"):
            if current:
                blocks.append(" ".join(current))
                current = []
        elif re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
            if current:
                blocks.append(" ".join(current))
                current = []
            blocks.append(line.strip())
        else:
            current.append(line.strip())
    if current:
        blocks.append(" ".join(current))
    problems = []
    for block in blocks:
        if len(block.split()) >= 12 and not re.search(r"(?<!\\)\[\d+(?:\s*[,–-]\s*\d+)*\](?!\()", block):
            problems.append("substantial text has no citation; cite supported notes or remove unsupported claims: " + block[:90])
    return problems


def main(argv):
    report_path = argv[1] if len(argv) > 1 else REPORT
    sources_path = argv[2] if len(argv) > 2 else SOURCES
    try:
        with open(report_path, encoding="utf-8") as f:
            report = f.read()
        with open(sources_path, encoding="utf-8") as f:
            sources = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"cannot read inputs: {exc}")
        return 1
    problems = check(report, sources) + check_structure(report) + check_citation_coverage(report)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"OK: {len(sources)} sources, all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
