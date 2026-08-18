---
name: office-tells
description: >
  Mandatory anti-AI quality gate for every PowerPoint (.pptx), Word (.docx), and Excel
  (.xlsx) file Claude creates or edits. Strips the visual, structural, and metadata tells
  that mark a document as machine-generated: pipe separators, em dashes, accent lines under
  slide titles, beige/default-blue/default-grey color choices, zebra table banding, excessive
  conditional formatting, Sheet1 names, library-default file metadata, hardcoded totals, and
  boilerplate section names. Use this skill BEFORE writing any code or content whenever the
  user asks to build, create, generate, make, write, edit, update, or produce a deck, slides,
  presentation, slideshow, pitch deck, PowerPoint, Word doc, document, report, memo, letter,
  brief, one-pager, template, spreadsheet, Excel file, workbook, financial model, tracker,
  budget, dashboard, or any .pptx/.docx/.xlsx file. Triggers even when the user does NOT
  mention "human," "natural," or "anti-AI" wording, the file type alone is the trigger. This
  is a behavioral overlay on the pptx, docx, and xlsx skills: read the relevant format skill
  for technical instructions, then apply every rule here. Always load this skill for Office
  file output. Do not generate a .pptx, .docx, or .xlsx without it.
author: Brian Aber
---

# Office Tells, Anti-AI Quality Gate

This skill is a **behavioral overlay** on top of the pptx, docx, and xlsx skills.
It does not replace them, it constrains them.
Read the relevant format skill first for technical instructions, then apply every rule in this file before writing a single line of code or content.

---

## Universal Rules (All Three Formats)

### No Vertical Pipe Separators
- **Never use `|` as a visual separator** in headers, footers, subtitles, or body text (e.g., `Q1 Results | Finance | Confidential`)
- This is one of the single strongest AI giveaways across all document types
- Use commas, line breaks, or separate text boxes/cells instead
- Exception: pipe characters inside code blocks or formula syntax are fine

### No Em Dashes
- **Never use em dashes (`—`)** anywhere in document content: body text, headers, callouts, table cells, slide text, or labels
- Em dashes are one of the most reliable signals that an AI wrote the content
- Use a comma, a colon, parentheses, or a new sentence instead
- Exception: em dashes that appear in data the user provided (e.g., a quoted passage or imported text) can stay as-is

### Document Metadata
- File properties are the most reliable machine tell that survives every visual fix. Anyone who opens File > Properties sees them. Set them on every file.
- **Never leave the library default or a blank author.** python-pptx, python-docx, and openpyxl stamp empty or library-named authors by default.
- Set a plausible author: the user's name or organization if known, otherwise a neutral realistic value. Never the literal library string, never blank.
- **`created` and `modified` must not be identical to the second.** AI output stamps them the same; real documents are edited over time. Offset `modified` from `created` by a realistic interval.
- Do not leave a default epoch timestamp (1970, 2000, or UTC midnight).
- Where to set it:
  - python-pptx: `prs.core_properties.author`, `.last_modified_by`, `.created`, `.modified`, `.revision`
  - python-docx: `doc.core_properties.author`, `.last_modified_by`, `.created`, `.modified`
  - openpyxl: `wb.properties.creator`, `.lastModifiedBy`, `.created`, `.modified`

### Document-Specific Language
This skill owns structural language: slide titles, section headers, sheet names, table labels, callouts. Sentence-level prose voice is delegated to the **human-tone** skill, apply it to any paragraph or body copy.
- No boilerplate section names (Introduction, Overview, Background, Conclusion, Agenda) unless the user asks for them
- Titles and headers state what the section actually says, not its function ("What We Found," not "Findings Overview")
- First line of any body block delivers information, context comes after the substance, not before
- For all running prose, defer to human-tone

### Data Realism
- When generating example or placeholder figures, make them lumpy. Real data is uneven.
- Avoid suspiciously round or evenly-spaced numbers (10/20/30, 1.2M/2.4M/3.6M). These read as fabricated.

---

## PowerPoint (PPTX)

### Layout and Structure
- **Vary slide layouts**, never repeat the same layout more than twice in a row. Alternate between columns, callouts, grids, and image-dominant structures.
- **No title-only slides followed by a bullet dump.** If bullets exist, pair them with a visual element on the same slide.
- **No "Introduction / Agenda / Conclusion" slides** unless the user explicitly requests them. Replace with action-oriented titles ("What We Found," "The Ask," "Three Things to Know").

### Bullets
- **Vary bullet count per slide.** Every slide carrying exactly three bullets is a tell.
- **Vary bullet length.** Bullets of near-equal length across a slide read as machine-generated. Mix short and long.

### Visual Anti-Patterns, Never Do These
- **No accent lines under slide titles.** The thin horizontal rule below a title is the single most reliable AI slide tell. Use whitespace or background contrast instead.
- **No full-width decorative bars or colored header/footer bands.** These read as AI template filler. If section breaks are needed, use background color changes or bold typography.
- **No cream, beige, or warm-neutral default backgrounds.** Off-white defaults (`F5F5DC`, `FAF0E6`, `FAEBD7`, `FFF8E1`) signal auto-generation. Use `FFFFFF` or the brand palette.
- **No equal-weight color palettes.** One color must dominate (60-70% visual weight), accent colors are accents, not equals.
- **No generic corporate blue as a default.** If no brand palette is specified, make a deliberate, topic-informed choice from the palette table in the pptx skill.

### Typography
- **No Arial as a default heading font.** Arial as body is acceptable, but headings need personality. Use Georgia, Trebuchet MS, Cambria, or Palatino unless brand specifies otherwise.
- Title size must visibly dominate body text (36pt+ vs 14-16pt). Flat size hierarchy is an AI tell.

### Speaker Notes
- Empty speaker notes on every slide is a tell. Either populate them with substance or leave them off deliberately, not auto-blank on all slides.

---

## Word (DOCX)

### Structure
- **No "Introduction / Overview / Background / Conclusion" as section headers.** Use specific, descriptive headers that tell the reader what the section actually says.
- **No uniform section depth.** Not every section needs a sub-section, vary the hierarchy based on content weight.
- **No opening paragraph that restates the document title.** The first sentence should deliver information, not announce intent.

### Visual Design
- **No overly colorful design.** Maximum two accent colors in any document. Colored headings, colored table headers, and colored callout boxes should not all appear together, pick one and commit.
- **No alternating white/grey table row banding** (e.g., openpyxl/docx default zebra stripes). This is the default AI table style. Use clean single-color headers with no-fill rows, or a simple top/bottom border on the header row only.
- **No rainbow section dividers or decorative colored rules.** A single thin grey rule (`CCCCCC`) or whitespace is sufficient.
- **No mismatched font colors across sections.** Stick to black body text with one optional accent color for headers or callouts. Never let headings, subheadings, and callouts each have their own color.

### Tables
- Preferred table style: white fill on all rows, light grey (`DDDDDD` or `EEEEEE`) header fill, single-color thin border (`CCCCCC`), no banding
- Cell padding should feel roomy (`top: 80, bottom: 80, left: 120, right: 120` in DXA), cramped cells are an AI tell
- No merged cells for visual effect, only merge when the data structure requires it

---

## Excel (XLSX)

### Visual Design
- **No overly colorful design.** A spreadsheet is not a dashboard. Limit intentional color to: one header fill color, one accent for totals/subtotals, and the standard blue/black/green/red formula color coding from the xlsx skill. No rainbow column headers, no alternating-color section blocks.
- **No excessive conditional formatting.** Conditional formatting should highlight genuine exceptions (top 10%, negative values, past-due dates). Do not apply gradient scales, icon sets, or data bars to every numeric column as decoration. Maximum two conditional formatting rules per sheet unless the user's use case requires more.
- **No openpyxl default grey header fill** (`D3D3D3` / `C0C0C0`). Use a deliberate color that matches the document's purpose (navy for financial models, light blue for operational trackers, etc.).

### Structure and Polish
- **Sheet names must be specific and human**, never `Sheet1`, `Sheet2`. Use names like `P&L`, `Assumptions`, `Revenue Build`, `COA`.
- **Freeze top row and/or first column** whenever the sheet has headers and more than ~15 rows of data.
- **Set column widths to content**, auto-fit then round to clean widths (e.g., 12, 18, 24). Uniform default widths signal machine generation.
- **Avoid merged cells for headers.** Use `center across selection` alignment instead, or simply bold the leftmost cell and leave others empty.

### Formulas
- **Totals and subtotals must be live formulas** (`=SUM()`), never hardcoded computed values. A human model calculates, AI often types the answer. Hardcoded totals where a formula belongs are a tell.

### Number Formatting
- Apply number formatting from the xlsx skill rules (accounting format, zero as `-`, percentages to one decimal). Unformatted raw numbers are an instant tell.
- Years and period labels should always be text strings, never formatted numbers.

---

## Final Check Before Delivering Any File

**Render and look. Do not skip this.** You generate these files blind through python libraries and cannot trust that the visual rules held. Before delivering:

1. Convert the file to images: LibreOffice headless to PDF (`soffice --headless --convert-to pdf`), then PDF to PNG per page/slide.
2. Actually view the images and check them against the list below. The visual rules are unenforceable without this step.
3. Open File > Properties (or inspect core properties in code) and confirm metadata is set.

- [ ] No pipe separators anywhere
- [ ] No em dashes anywhere in generated content
- [ ] Metadata set: real author, created and modified differ, no library defaults
- [ ] No default AI color choices (generic blue, beige, default grey fills)
- [ ] No alternating zebra row banding in Word tables
- [ ] No excessive conditional formatting or rainbow color blocks in Excel
- [ ] Excel totals are live formulas, not hardcoded
- [ ] No accent lines under PowerPoint titles
- [ ] Bullet counts and lengths vary across slides
- [ ] No boilerplate section names (Introduction, Overview, Conclusion)
- [ ] Typography has real hierarchy, title vs body sizes visibly different
- [ ] Sheet names, slide titles, and section headers are specific and descriptive
- [ ] Example data is lumpy, not suspiciously round or evenly spaced
- [ ] You rendered the file to images and looked at it

---

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/office-tells/).
