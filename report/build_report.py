"""Build the CMP7200 project dissertation.

    python build_report.py

Renders every figure, reads the measured experiment statistics, assembles the
document and writes CMP7200_Project_Report.docx alongside this script.

No result is typed into the prose by hand. Chapter 6 reads
InterviewAI/experiments/results/statistics.json, so re-running the evaluation
harness and rebuilding produces a document consistent with the new numbers.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / "InterviewAI"
FIGURES = HERE / "figures"
EXP_FIGURES = PROJECT / "experiments" / "figures"
RESULTS = PROJECT / "experiments" / "results"
STATS_PATH = RESULTS / "statistics.json"
OUTPUT = HERE / "CMP7200_Project_Report.docx"

sys.path.insert(0, str(HERE))

from docx_kit import add_page_numbers, new_document  # noqa: E402
import content_part1 as p1  # noqa: E402
import content_part2 as p2  # noqa: E402
import content_part3 as p3  # noqa: E402
import content_ch6  # noqa: E402


def fig(name: str, experiments: bool = False) -> Path:
    """Resolve a figure by stem, from either figure directory."""
    root = EXP_FIGURES if experiments else FIGURES
    path = root / f"{name}.png"
    if not path.exists():
        raise FileNotFoundError(
            f"Figure '{name}' not found at {path}. "
            f"Run diagrams.py, or the evaluation harness for result figures."
        )
    return path


def load_json(path: Path, label: str) -> dict:
    """Load a tracked evidence fixture, warning rather than failing if absent."""
    if not path.exists():
        print(f"  ! {label} not found at {path} — the section using it will be thin.")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_stats() -> dict | None:
    if not STATS_PATH.exists():
        print(f"  ! No statistics at {STATS_PATH} — Chapter 6 will note the omission.")
        return None
    return json.loads(STATS_PATH.read_text(encoding="utf-8"))


def run_test_suite() -> dict:
    """Run the unit tests so the reported count is measured, not asserted."""
    python = PROJECT / "venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    try:
        proc = subprocess.run(
            [str(python), "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=str(PROJECT), capture_output=True, text=True, timeout=600,
        )
        match = re.search(r"(\d+) passed", proc.stdout)
        count = int(match.group(1)) if match else None
        failed = re.search(r"(\d+) failed", proc.stdout)
        return {
            "count": count,
            "failed": int(failed.group(1)) if failed else 0,
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        print(f"  ! Could not run the test suite: {exc}")
        return {}


def ensure_diagrams():
    expected = [f"fig{n:02d}" for n in range(1, 12)]
    have = {p.stem[:5] for p in FIGURES.glob("*.png")} if FIGURES.exists() else set()
    if not all(e in have for e in expected):
        print("  Rendering architecture figures...")
        import diagrams
        diagrams.main()


def word_count(doc) -> int:
    """Body word count in document order.

    The brief counts everything in the main body including headings, tables
    and lists, and excludes the front matter and everything from the
    references onward. Tables are not interleaved with doc.paragraphs, so the
    body XML is walked directly to get the ordering right.
    """
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    words, counting = 0, False
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            para_obj = Paragraph(child, doc)
            text = para_obj.text.strip()
            # Only real chapter headings are markers — the identical strings in
            # the table of contents must not start or stop the count.
            is_h1 = para_obj.style.name == "Heading 1"
            if is_h1 and text.startswith("1.  Introduction"):
                counting = True
            elif is_h1 and text == "References":
                break
            if counting and text:
                words += len(text.split())
        elif tag == "tbl" and counting:
            for row in Table(child, doc).rows:
                for cell in row.cells:
                    words += len(cell.text.split())
    return words


def main():
    print("Building CMP7200 project report")
    print("=" * 62)

    ensure_diagrams()

    stats = load_stats()
    if stats:
        meta = stats["meta"]
        usage = meta.get("api_usage", {})
        print(f"  Statistics loaded: {meta['n_graded_answers']} graded answers, "
              f"{usage.get('calls', '?')} API calls")

    print("  Running the test suite...")
    tests = run_test_suite()
    if tests.get("count"):
        state = "all passing" if tests.get("ok") else f"{tests.get('failed')} FAILING"
        print(f"  Tests: {tests['count']} ({state})")
    extra = {
        "tests": tests,
        "track_b": load_json(RESULTS / "track_b_evidence.json", "Track B evidence"),
        "worked_example": load_json(RESULTS / "worked_example.json", "worked example"),
    }

    doc = new_document()
    add_page_numbers(doc)

    print("  Front matter...")
    p1.front_matter(doc, fig, stats, extra)
    print("  Chapter 1  Introduction")
    p1.chapter_1(doc, fig)
    print("  Chapter 2  Literature Review")
    p1.chapter_2(doc, fig)
    print("  Chapter 3  Research Methodology")
    p2.chapter_3(doc, fig)
    print("  Chapter 4  System Design")
    p2.chapter_4(doc, fig)
    print("  Chapter 5  Implementation")
    p2.chapter_5(doc, fig)
    print("  Chapter 6  Evaluation and Results")
    content_ch6.chapter_6(doc, fig, stats, extra)
    print("  Chapter 7  Critical Reflection")
    p3.chapter_7(doc, fig, stats, extra)
    print("  Chapter 8  Conclusion and Future Work")
    p3.chapter_8(doc, fig, stats, extra)
    print("  References")
    p3.references(doc)
    print("  Appendices")
    p3.appendices(doc, fig, extra)

    target = OUTPUT
    try:
        doc.save(target)
    except PermissionError:
        # Word holds an exclusive lock on an open document. Write alongside it
        # rather than losing the build.
        target = OUTPUT.with_name(OUTPUT.stem + "_NEW.docx")
        doc.save(target)
        print(f"\n  ! {OUTPUT.name} is open in Word and could not be overwritten.")
        print(f"  ! Written to {target.name} instead — close Word, delete the old "
              f"file and rename this one.\n")

    count = word_count(doc)
    print("=" * 62)
    print(f"  Written: {target}")
    print(f"  Body word count (Ch.1 to Ch.8, incl. tables): ~{count:,}")
    limit, tolerance = 12000, 13200
    if count > tolerance:
        print(f"  ! Over the 12,000 + 10% limit by {count - tolerance:,} words")
    elif count < limit * 0.9:
        print(f"  ! {limit - count:,} words below the 12,000 target")
    else:
        print(f"  Within the 12,000 word limit and its 10% tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
