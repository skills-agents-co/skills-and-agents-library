#!/usr/bin/env python3
"""Extract structured keyword data from a job description.

Reads JD text on stdin and writes a JSON object on stdout with:
  - must_have:        noun chunks from Requirements / Qualifications / You have
  - nice_to_have:     noun chunks from Nice to have / Preferred sections
  - seniority_signals: years-of-experience patterns + role-level words
  - domain_signals:    capitalized acronyms and proper nouns (deduped)

Requires: spacy>=3.7 and the en_core_web_sm model.
    pip install -r requirements.txt
    python -m spacy download en_core_web_sm
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple

import spacy


SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("must_have", re.compile(r"^\s*(requirements|qualifications|you\s+have|what\s+you'?ll\s+need|minimum\s+qualifications|basic\s+qualifications|must\s+have)s?\b[:\s]*$", re.IGNORECASE | re.MULTILINE)),
    ("nice_to_have", re.compile(r"^\s*(nice\s+to\s+have|preferred|bonus|preferred\s+qualifications|nice-to-have|pluses?)s?\b[:\s]*$", re.IGNORECASE | re.MULTILINE)),
    ("responsibilities", re.compile(r"^\s*(responsibilities|what\s+you'?ll\s+do|the\s+role|role\s+overview|about\s+the\s+role)s?\b[:\s]*$", re.IGNORECASE | re.MULTILINE)),
]

YOE_PATTERN = re.compile(
    r"(\d+\+?\s*(?:-\s*\d+\s*)?years?\s+(?:of\s+)?(?:[a-zA-Z][a-zA-Z\s/+\-]{1,40}?\s+)?experience)",
    re.IGNORECASE,
)
ROLE_LEVEL_WORDS = ["senior", "staff", "lead", "principal", "head of", "director", "vp", "chief"]

ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}\b")

STOPWORD_CHUNKS = {
    "we", "you", "the team", "our team", "the company", "the role", "the position",
    "a great", "a strong", "an opportunity", "your work", "this role", "the work",
    "things", "people", "us", "it", "everything", "anything",
}


def split_sections(text: str) -> Dict[str, str]:
    """Split text into sections keyed by section_type using header regexes.

    Anything before the first matched header goes into the 'preamble' bucket.
    Returns a dict {section_type: concatenated text}. A given section_type may
    appear multiple times in the JD; we concat them.
    """
    matches: List[Tuple[int, int, str]] = []  # (start, end_of_header, section_type)
    for section_type, pattern in SECTION_PATTERNS:
        for m in pattern.finditer(text):
            matches.append((m.start(), m.end(), section_type))
    matches.sort()

    sections: Dict[str, List[str]] = {"preamble": []}
    if not matches:
        sections["preamble"].append(text)
    else:
        if matches[0][0] > 0:
            sections["preamble"].append(text[: matches[0][0]])
        for i, (_start, header_end, section_type) in enumerate(matches):
            next_start = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            body = text[header_end:next_start]
            sections.setdefault(section_type, []).append(body)

    return {k: "\n".join(v) for k, v in sections.items()}


def noun_chunks(nlp, text: str) -> List[str]:
    if not text.strip():
        return []
    doc = nlp(text)
    chunks: List[str] = []
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        # Strip leading articles / determiners
        phrase = re.sub(r"^(a|an|the|our|your|their|this|that|these|those)\s+", "", phrase)
        phrase = phrase.strip(" .,:;-")
        if len(phrase) < 3:
            continue
        if phrase in STOPWORD_CHUNKS:
            continue
        if not re.search(r"[a-z]", phrase):
            continue
        chunks.append(phrase)
    return chunks


def rank_by_frequency(chunks: List[str]) -> List[str]:
    counter = Counter(chunks)
    return [c for c, _ in counter.most_common()]


def extract_seniority_signals(text: str) -> List[str]:
    signals: List[str] = []
    for m in YOE_PATTERN.finditer(text):
        signals.append(m.group(1).strip().lower())
    lower = text.lower()
    for word in ROLE_LEVEL_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            signals.append(word)
    seen = set()
    out = []
    for s in signals:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def extract_domain_signals(text: str) -> List[str]:
    acronyms = ACRONYM_PATTERN.findall(text)
    # Filter common English ALL-CAPS words
    blocklist = {"YOU", "WE", "OUR", "THE", "AND", "OR", "FOR", "WITH", "PTO", "USA", "US"}
    seen = set()
    out: List[str] = []
    for a in acronyms:
        if a in blocklist:
            continue
        if a in seen:
            continue
        seen.add(a)
        out.append(a)
    return out


def main() -> int:
    text = sys.stdin.read()
    if not text.strip():
        print(json.dumps({"error": "no input on stdin"}))
        return 1

    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print(
            json.dumps(
                {
                    "error": "spacy model 'en_core_web_sm' not installed. Run: python -m spacy download en_core_web_sm"
                }
            )
        )
        return 1

    sections = split_sections(text)

    must_have_text = sections.get("must_have", "")
    nice_to_have_text = sections.get("nice_to_have", "")

    must_have = rank_by_frequency(noun_chunks(nlp, must_have_text))
    nice_to_have = rank_by_frequency(noun_chunks(nlp, nice_to_have_text))

    # Deduplicate nice_to_have against must_have
    must_have_set = set(must_have)
    nice_to_have = [c for c in nice_to_have if c not in must_have_set]

    output = {
        "must_have": must_have,
        "nice_to_have": nice_to_have,
        "seniority_signals": extract_seniority_signals(text),
        "domain_signals": extract_domain_signals(text),
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
