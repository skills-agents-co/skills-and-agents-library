#!/usr/bin/env python3
"""Render tailored resume + cover letter markdown to ATS-safe PDFs.

CLI:
  --resume PATH           markdown file for the tailored resume
  --cover-letter PATH     markdown file for the cover letter
  --out-dir PATH          directory to write the two PDFs into
  --role "Senior PM"      role name; used to derive the output file slug

Output files:
  <role-slug>_resume.pdf
  <role-slug>_cover_letter.pdf

Formatting (enforced by inline CSS):
  - Single column
  - System fonts only (Helvetica/Arial fallback)
  - No tables, no images
  - Plain H1/H2
  - No headers/footers
"""

from __future__ import annotations

import argparse
import os
import re
import sys

try:
    import markdown  # type: ignore
except ImportError:
    print("Missing dependency 'markdown'. Install: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

try:
    from weasyprint import HTML  # type: ignore
except ImportError:
    print(
        "Missing dependency 'weasyprint'. Install: pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)


ATS_SAFE_CSS = """
@page {
    margin: 0.5in;
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #000;
    max-width: 7.5in;
    margin: 0.5in auto;
}
h1 {
    font-family: inherit;
    font-size: 18pt;
    margin: 0 0 0.1in 0;
}
h2 {
    font-family: inherit;
    font-size: 13pt;
    margin: 0.2in 0 0.05in 0;
    border-bottom: 1px solid #000;
}
h3 {
    font-family: inherit;
    font-size: 11pt;
    margin: 0.15in 0 0.05in 0;
}
p, li {
    font-family: inherit;
    font-size: 11pt;
}
ul {
    padding-left: 1.2em;
    margin: 0.05in 0;
}
table, img {
    display: none;
}
"""


def slugify(role: str) -> str:
    s = role.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "role"


def render_one(md_path: str, out_path: str) -> None:
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    html_body = markdown.markdown(md_text, extensions=["extra"])
    full_html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>{ATS_SAFE_CSS}</style></head>"
        f"<body>{html_body}</body></html>"
    )
    HTML(string=full_html).write_pdf(out_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", required=True)
    parser.add_argument("--cover-letter", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--role", required=True)
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    slug = slugify(args.role)

    resume_out = os.path.join(args.out_dir, f"{slug}_resume.pdf")
    cover_out = os.path.join(args.out_dir, f"{slug}_cover_letter.pdf")

    render_one(args.resume, resume_out)
    render_one(args.cover_letter, cover_out)

    print(resume_out)
    print(cover_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
