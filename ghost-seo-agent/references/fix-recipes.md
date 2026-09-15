## Fix Recipes (Step 5)

#### Fix A — Missing meta description
If `meta_description` is null or empty:

Generate a meta description:
- 140-155 characters
- Includes the primary keyword (infer from title + first paragraph)
- Specific — names the product, player, team, or topic
- Does not start with "In this post" or "Learn how"

Apply:
```
ghost-mcp:posts_edit → id: [post_id], meta_description: [generated]
```

#### Fix B — Missing custom excerpt
If `custom_excerpt` is null:

Generate a 1-2 sentence excerpt that:
- Leads with the most specific/interesting fact from the post
- Is distinct from the meta description (not a copy-paste)
- Under 300 characters

Apply:
```
ghost-mcp:posts_edit → id: [post_id], custom_excerpt: [generated]
```

#### Fix C — Title too long
If `title` > 60 characters and `meta_title` is null:

Generate a meta title that:
- Is under 60 characters
- Preserves the primary keyword
- Doesn't truncate mid-word in Google's SERP display

Apply:
```
ghost-mcp:posts_edit → id: [post_id], meta_title: [shortened title]
```

#### Fix D — No feature image (flag only, don't auto-apply)
If `feature_image` is null: add to the manual fix list. Do not attempt to
auto-assign images — image selection requires editorial judgment.

#### Fix E — Members-only post with no excerpt
If `visibility` is `members` or `paid` and `custom_excerpt` is null:

Generate a 1-2 sentence teaser excerpt that:
- Describes what the post covers without giving away the full content
- Functions as a standalone hook for search results
- Under 300 characters

Apply:
```
ghost-mcp:posts_edit → id: [post_id], custom_excerpt: [generated teaser]
```

#### Fix F — Feature image not WebP (flag only)
If `feature_image` URL doesn't end in `.webp`: add to manual fix list with note
"Re-upload as WebP to improve LCP score." Do not attempt to convert or re-upload
images — this requires editorial action outside Ghost MCP.
