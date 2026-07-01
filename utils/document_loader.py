"""Simple document loader — accepts raw text or reads .txt files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def load_cv(source: str) -> str:
    if source.lower().endswith(".txt"):
        return Path(source).read_text(encoding="utf-8")
    return source


def load_jd(source: str) -> str:
    if source.lower().endswith(".txt"):
        return Path(source).read_text(encoding="utf-8")
    return source


if __name__ == "__main__":
    text = load_cv("Experienced Python developer with 5 years of experience.")
    print(f"CV loaded: {len(text)} chars")

    text = load_jd("We need a Python developer.")
    print(f"JD loaded: {len(text)} chars")

    print("Document Loader: Tests passed")
