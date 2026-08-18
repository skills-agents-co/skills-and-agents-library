# ATS Do's and Don'ts

Applicant Tracking Systems parse PDFs as if they were plain text. Anything that breaks the parser silently downgrades your resume. These rules are enforced by `scripts/render_pdf.py`; do not override them.

## Do

1. Use a single column for the entire document.
2. Use system fonts only (Helvetica or Arial). They render reliably on every parser.
3. Use plain `# H1` for your name and `## H2` for section headers (Summary, Experience, Skills, Education).
4. Use a bulleted list (`-`) for accomplishments under each role.
5. Put dates in plain text on their own line (e.g., `Jan 2022 – Present`).
6. Spell out acronyms the first time they appear, then use the acronym (e.g., "Applicant Tracking System (ATS)").
7. Save and submit as PDF unless the application explicitly asks for .docx.

## Don't

1. Don't use multi-column layouts. Parsers read top-to-bottom; columns get scrambled.
2. Don't use tables for any structural layout. Tables routinely break parsing.
3. Don't use text boxes, sidebars, or shapes.
4. Don't include images, logos, headshots, or icons.
5. Don't use page headers or footers — they are commonly skipped or duplicated by parsers.
6. Don't use custom or decorative fonts. The parser may substitute and break spacing.
7. Don't put your contact info inside a header element. Put it as plain text under your name.
8. Don't use special characters for bullets (e.g., diamonds, arrows). Use a plain hyphen or the default markdown list.
9. Don't combine the cover letter and resume into a single PDF. Two files, two uploads.
10. Don't password-protect the PDF.
