"""Run the five preset topics sequentially; --resume skips validated outputs."""
import argparse

from check_citations import check, check_citation_coverage, check_structure
from research import REPORTS, main as run_topic
from self_check import check_topic, load_topics


def validate_report(text, sources):
    return check(text, sources) + check_structure(text) + check_citation_coverage(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", action="store_true", help="skip reports that pass local rubric checks")
    args = parser.parse_args(argv)
    topics = load_topics()
    if not topics:
        print("No topics found in topics.md")
        return 1
    for index, topic in enumerate(topics, 1):
        if args.resume and not check_topic(topic, REPORTS, validate_report):
            print(f"[{index}/{len(topics)}] Already validated: {topic}", flush=True)
            continue
        print(f"[{index}/{len(topics)}] Running: {topic}", flush=True)
        code = run_topic(topic)
        if code:
            print("Stopped at a failed topic. Fix the cause and rerun with --resume.")
            return code
    print("All preset topics completed. Next: python self_check.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
