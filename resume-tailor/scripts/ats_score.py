#!/usr/bin/env python3
"""Score a resume's ATS keyword coverage against extracted JD keywords.

Inputs:
  --keywords PATH    JSON file produced by extract_jd_keywords.py
  --resume   PATH    plain-text resume (markdown is fine; we lowercase + tokenize)

Output (stdout, JSON):
  {
    "coverage_pct": float,            # matched_must_have / total_must_have, 0.0 if no must_have
    "matched_must_have": [...],
    "missing_must_have": [...],
    "matched_nice_to_have": [...],
    "missing_nice_to_have": [...],
    "suggestions": [...]              # short, generic suggestions for top missing items
  }
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import List, Tuple


def whole_phrase_present(phrase: str, resume_lower: str) -> bool:
    """Substring match with word boundaries on a lowercased resume."""
    if not phrase:
        return False
    # Escape regex chars; allow flexible whitespace inside the phrase
    parts = [re.escape(tok) for tok in phrase.split()]
    pattern = r"\b" + r"\s+".join(parts) + r"\b"
    return re.search(pattern, resume_lower) is not None


def partition(items: List[str], resume_lower: str) -> Tuple[List[str], List[str]]:
    matched: List[str] = []
    missing: List[str] = []
    for p in items:
        if whole_phrase_present(p, resume_lower):
            matched.append(p)
        else:
            missing.append(p)
    return matched, missing


def suggestions_for(missing: List[str]) -> List[str]:
    out = []
    for kw in missing[:5]:
        out.append(
            f"If you have legitimate experience with '{kw}', surface it in your Summary or a bullet under Experience."
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--resume", required=True)
    args = parser.parse_args()

    with open(args.keywords, "r", encoding="utf-8") as f:
        kw = json.load(f)
    with open(args.resume, "r", encoding="utf-8") as f:
        resume_text = f.read()

    resume_lower = resume_text.lower()

    must_have: List[str] = kw.get("must_have", []) or []
    nice_to_have: List[str] = kw.get("nice_to_have", []) or []

    matched_mh, missing_mh = partition(must_have, resume_lower)
    matched_nh, missing_nh = partition(nice_to_have, resume_lower)

    coverage = (len(matched_mh) / len(must_have)) if must_have else 0.0

    output = {
        "coverage_pct": round(coverage, 4),
        "matched_must_have": matched_mh,
        "missing_must_have": missing_mh,
        "matched_nice_to_have": matched_nh,
        "missing_nice_to_have": missing_nh,
        "suggestions": suggestions_for(missing_mh),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
