"""Build the CMP7200 project dissertation.

    python build_report.py

Renders every figure, reads the measured experiment statistics, assembles the
document and writes CMP7200_Project_Report.docx into submission/.

That is the generated draft, not the submission. The submitted dissertation
is submission/AI-Interview.docx, which was finished by hand. This script
deliberately does not write to that filename: running it would overwrite
those edits. Regenerate here, then carry any changes across by hand.

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
PROJECT = HERE.parent.parent / "InterviewAI"
FIGURES = HERE / "figures_png"
EXP_FIGURES = PROJECT / "experiments" / "figures"
SCREENSHOTS = HERE / "screenshots"   # captured from the running app, not generated
RESULTS = PROJECT / "experiments" / "results"
STATS_PATH = RESULTS / "statistics.json"
OUTPUT = HERE.parent / "CMP7200_Project_Report.docx"

sys.path.insert(0, str(HERE))

from document_toolkit import add_page_numbers, new_document  # noqa: E402
import front_matter          # noqa: E402
import chapter1_introduction       # noqa: E402
import chapter2_literature         # noqa: E402
import chapter3_methodology        # noqa: E402
import chapter4_design             # noqa: E402
import chapter5_implementation     # noqa: E402
import chapter6_evaluation         # noqa: E402
import chapter7_reflection         # noqa: E402
import chapter8_conclusion         # noqa: E402
import back_matter            # noqa: E402


def fig(name: str, experiments: bool = False) -> Path:
    """Resolve a figure by stem.

    Three sources: architecture diagrams rendered by figures.py, result charts
    from the evaluation harness, and screenshots captured from the running
    application. The screenshots are kept in version control because, unlike
    the other two, they cannot be regenerated without standing the system up.
    """
    for root in ((EXP_FIGURES,) if experiments else (FIGURES, SCREENSHOTS)):
        path = root / f"{name}.png"
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Figure '{name}' not found. Run figures.py, the evaluation harness "
        f"for result charts, or capture the interface for a screenshot."
    )


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
        import figures
        figures.main()


def ensure_result_figures():
    """Redraw the five experiment charts if they are missing.

    Both the charts and the architecture diagrams are build output and are not
    kept in version control, but these come from the evaluation harness rather
    than from figures.py. Re-running the harness properly would cost API calls;
    --figures-only re-reads the tracked raw_scores.json and redraws from it, so
    a fresh clone can rebuild the dissertation for nothing.
    """
    expected = ["e1_discriminant_validity", "e2_positional_bias",
                "e3_paraphrase_invariance", "e4_criterion_correlation",
                "e5_verbosity"]
    have = {p.stem for p in EXP_FIGURES.glob("*.png")} if EXP_FIGURES.exists() else set()
    missing = [e for e in expected if e not in have]
    if not missing:
        return
    if not (PROJECT / "experiments" / "results" / "raw_scores.json").exists():
        print(f"  ! {len(missing)} result figure(s) missing and no cached scores "
              f"to redraw them from. Run the evaluation harness.")
        return
    print(f"  Redrawing {len(missing)} result figure(s) from cached scores...")
    python = PROJECT / "venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    proc = subprocess.run(
        [str(python), "-m", "experiments.run_evaluation", "--figures-only"],
        cwd=str(PROJECT), capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        print(f"  ! Redraw failed:\n{proc.stdout[-600:]}{proc.stderr[-600:]}")


def measure_code() -> dict:
    """Count the artefact as it actually stands.

    Chapter 5 previously stated the size of the implementation from memory, and
    both figures had drifted from the code. Measuring at build time keeps that
    claim honest for the same reason every result in Chapter 6 is read from the
    results file rather than typed.
    """
    def lines(path: Path, code_only: bool = True) -> int:
        try:
            text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return 0
        if not code_only:
            return len(text)
        return len([l for l in text
                    if l.strip() and not l.strip().startswith(("#", "//", "*", "/*"))])

    skip = ("venv", "__pycache__", "node_modules", "dist")
    py = sum(lines(p, False) for p in PROJECT.rglob("*.py")
             if not any(s in str(p) for s in skip))
    js = sum(lines(p, False) for p in (PROJECT / "frontend" / "src").rglob("*.js*"))

    modules = [
        ("M1", "CV parsing", "core/agents/cv_parser.py"),
        ("M2", "Job description parsing", "core/agents/jd_parser.py"),
        ("M3", "Skill graph and matching", "core/graph/skill_graph.py"),
        ("M4", "Question generation", "core/agents/question_generator.py"),
        ("M5", "Voice interview agent", "core/livekit/voice_agent.py"),
        ("M5t", "Text interview engine", "core/pipeline/text_interview.py"),
        ("M6", "Answer judge", "core/evaluator/answer_judge.py"),
        ("M6a", "Skill state tracker", "core/graph/skill_state.py"),
        ("M7/M8", "Attention and posture", "frontend/src/lib/vision.js"),
        ("M9", "Behavioural integrity", "core/evaluator/behavioural_integrity.py"),
        ("M10", "Vocal delivery", "frontend/src/lib/voice.js"),
        ("M11", "Weighted fusion", "core/evaluator/score_fusion.py"),
        ("M12", "Report assembly", "core/report/report_builder.py"),
    ]
    rows = [(tag, name, rel.rsplit("/", 1)[-1], lines(PROJECT / rel))
            for tag, name, rel in modules]
    return {"python": py, "javascript": js, "modules": rows,
            "module_total": sum(r[3] for r in rows)}


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
    ensure_result_figures()

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
        "code": measure_code(),
    }

    doc = new_document()
    add_page_numbers(doc)

    for label, render in (
        ("Front matter",                  lambda: front_matter.front_matter(doc, fig, stats, extra)),
        ("Chapter 1  Introduction",       lambda: chapter1_introduction.chapter_1(doc, fig)),
        ("Chapter 2  Literature Review",  lambda: chapter2_literature.chapter_2(doc, fig)),
        ("Chapter 3  Methodology",        lambda: chapter3_methodology.chapter_3(doc, fig)),
        ("Chapter 4  System Design",      lambda: chapter4_design.chapter_4(doc, fig)),
        ("Chapter 5  Implementation",     lambda: chapter5_implementation.chapter_5(doc, fig, extra)),
        ("Chapter 6  Evaluation",         lambda: chapter6_evaluation.chapter_6(doc, fig, stats, extra)),
        ("Chapter 7  Reflection",         lambda: chapter7_reflection.chapter_7(doc, fig, stats, extra)),
        ("Chapter 8  Conclusion",         lambda: chapter8_conclusion.chapter_8(doc, fig, stats, extra)),
        ("References",                    lambda: back_matter.references(doc)),
        ("Appendices",                    lambda: back_matter.appendices(doc, fig, extra)),
    ):
        print(f"  {label}")
        render()

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
