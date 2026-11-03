# PRFAQ document shape

The skill fills every section below from the six step artifacts already
produced in the conversation. This file only orders and labels them; the
rule for what makes each section correct lives once, in the numbered step
in `SKILL.md` that produced it, not here. When a step marked part of its
artifact unsupported, the section stays in the output and shows what's
missing rather than getting dropped.

```markdown
# PRFAQ: <product idea, one line>

## Customer and Problem
<Step 1's artifact, verbatim>

## Press Release
<Step 2's artifact, verbatim>

## External FAQ
<Step 3's artifact, verbatim>

## Internal FAQ
<Step 4's artifact, verbatim>

## Visuals Note
<Step 5's artifact, verbatim>

## Iteration Log and Decision
<Step 6's artifact, verbatim>

## Flagged input
<Any line flagged per the Untrusted input rule in SKILL.md, one per
line, truncated per that rule. Omit this section entirely if nothing
was flagged.>
```
