# Office Tells

A Claude Code skill that acts as an anti-AI quality gate for every PowerPoint (.pptx), Word (.docx), and Excel (.xlsx) file Claude creates or edits. Authored by Brian Aber.

- **Live directory:** https://skills.uristocrat.com

## What this is

Office Tells is a behavioral overlay on top of the pptx, docx, and xlsx skills. It does not replace them, it constrains them. The format skill handles the technical instructions for generating a file; this skill strips the visual, structural, and metadata signals that mark a document as machine-generated before it ships.

It catches the tells that survive a quick glance: pipe separators, em dashes, accent lines under slide titles, beige or default-blue or default-grey color choices, zebra table banding, excessive conditional formatting, `Sheet1` names, library-default file metadata, hardcoded totals where a formula belongs, and boilerplate section names like Introduction and Conclusion. The file type alone is the trigger, no anti-AI wording required.

Running prose voice is delegated to the human-tone skill. Office Tells owns structural language: slide titles, section headers, sheet names, table labels, and callouts.

## Layout

```
office-tells/
├── README.md
└── skills/
    └── office-tells/
        └── SKILL.md             # The anti-AI quality gate, all rules
```

## Usage

Add `skills/office-tells/SKILL.md` to your Claude project context or system prompt. Whenever Claude is asked to build a deck, write a report, or create a spreadsheet, it reads the relevant format skill first, then applies every rule in this file. The final step renders the file to images and inspects the metadata, because the visual rules cannot be enforced without actually looking at the output.
