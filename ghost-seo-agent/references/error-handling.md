## Ghost MCP Error Handling

If `ghost-mcp:posts_edit` fails for a specific post:
- Log the failure with post ID and error message
- Continue to the next post — do not halt the entire run
- Include failed edits in the report under "Manual fixes required"

If Ghost MCP is completely unavailable:
- Complete Steps 1-4 (diagnosis) using browser only
- Skip Steps 5-6 (fixes)
- Produce a diagnosis-only report with a manual fix checklist

---

## Browser Navigation Fallbacks

If Search Console UI has changed:
- Use the search bar within Search Console to find "Pages" or "Coverage" report
- Adapt to UI changes — do not fail because a menu label changed

If Google requires re-authentication mid-session:
- Pause and notify the publisher
- Do not attempt to enter credentials
- Resume from the last completed step after the publisher re-authenticates
