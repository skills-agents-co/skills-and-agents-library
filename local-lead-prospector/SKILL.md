---
name: local-lead-prospector
description: Assembles an outreach list of local businesses for an SDR from an industry + region pair. Returns a CSV with name, category, address, phone, website, rating, review count, and a Google Maps source URL, plus a markdown summary. Listing data only. No decision-maker names, no personal emails, no LinkedIn scraping. The Google Places API (New) is the only path and requires GOOGLE_MAPS_API_KEY. Use this skill when an SDR asks to "find me dentists in Austin", "build a lead list for HVAC companies in Denver", "I need contacts for law firms in Chicago", "give me a prospecting list", or "who should I cold-call in this market". Do NOT trigger on single-consumer lookups like "find me a good dentist near me", "what is the best taco place in Austin", or "where should I take a client to dinner in SoHo". Those are one-shot recommendations, not lead lists.
---

# Local Lead Prospector

## Compliance up front

Google Maps listing data is the source, and there is one way to get it.

- **The only path: Google Places API (New).** Official, paid, billed per request. Requires `GOOGLE_MAPS_API_KEY` in the environment. Free tier is small, so a cost estimate is shown before any pull above 50 rows.

Without a key, this skill stops. Do not scrape Google Maps, and do not reach for a browser-automation workaround. There is no fallback path here on purpose.

Listing data only. Never produce decision-maker names, personal emails, or LinkedIn profiles. Enrichment past the public Google Maps listing is out of scope.

## What you get per business

Each row in the CSV:

- `name`
- `category` (primary type from Google)
- `address`
- `phone` (international format when Google has it, blank when missing)
- `website` (blank when missing)
- `rating` (0.0 to 5.0)
- `reviews` (count)
- `source_url` (Google Maps URL for this place)

Missing phone or website cells stay blank. Do not fabricate or guess values.

## Workflow

### 1. Confirm industry and region

Both must be specific. If either is vague, ask one clarifying question and stop.

- "Texas" is too broad. Ask for a city or metro.
- "small business" is too broad. Ask for an industry like "dentists", "HVAC", "law firms".
- "Austin, TX" is real.
- "dentists in Austin, TX" is ready to run.

### 2. Confirm count

Default is 40 rows. Ask only if the user has not stated a number. If the user asks for more than 100, push back and suggest splitting by sub-region (zip, neighborhood, adjacent city). Over 100 in one pull tends to hit the same dense cluster and waste cost.

### 3. Check for the API key

- If `GOOGLE_MAPS_API_KEY` is set, run the API path.
- If it is missing, stop. Tell the user the Google Places API (New) is the only way this skill pulls listings, and point them at `references/places_api_setup.md` to get a key. Do not look for another source.

### 4. Cost estimate before large pulls

If the requested count is above 50, surface the cost estimate first. Pricing tier is Places API (New) Text Search. At the time of writing, Text Search is billed per request and each request returns up to 20 results, so a 100-row pull is about 5 paginated requests. Show the estimate and ask the user to confirm before running.

### 5. Run the script

```
python scripts/fetch_places_api.py \
  --industry "dentists" \
  --region "Austin, TX" \
  --count 40 \
  --out leads.csv
```

### 6. Write the CSV and the summary

The script emits this CSV schema. Header line is byte-identical:

```
name,category,address,phone,website,rating,reviews,source_url
```

Then post the markdown summary in the chat (template below).

## Summary template

After the run, post this exact structure back to the user:

```
## Lead list: <industry> in <region>

- Total leads: <N>
- With phone: <P> (<P/N>%)
- With website: <W> (<W/N>%)
- Source: Google Places API (New)
- CSV: <path to leads.csv>

### Sample (first 10)

| Name | Category | Phone | Website | Rating | Reviews |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... |

### SDR notes

- Rows without a phone are usable for email-only sequences.
- Rows without a website are local, likely solo operators. Cold-call first.
- Ratings below 3.5 with high review counts often signal an operations gap, which is a real opening for a pitch about ops tooling.
- The CSV does not contain decision-maker names. Pair with manual LinkedIn lookups before sending personalized outreach.
```

Numbers are derived directly from the CSV that was written. Sample table is the first 10 rows. If fewer than 10 rows came back, show them all.

## Failure handling

Surface clear messages. Never dump a Python traceback at the user.

- **Zero rows.** Exit cleanly. Tell the user the query returned nothing and suggest a broader industry term or a wider region. No traceback.
- **No API key.** The script exits with a message naming the Google Places API (New) as the only path and pointing at `references/places_api_setup.md`. Pass that along as-is. Do not offer another way to get the data.
- **Over-broad region.** If the user is asking for a state or a country, do not run. Ask for a city or metro.
- **Over-volume.** If the user asks for more than 100, do not run. Suggest splitting by sub-region.
- **API quota exceeded.** Surface as "Google Places API quota exceeded for the current period. Either wait for reset or raise the quota in Google Cloud Console."
- **API billing not enabled.** HTTP 403 with "billing" in the body. Surface as "Google Places API billing is not enabled on this Cloud project. See references/places_api_setup.md."
- **API key invalid.** `API_KEY_INVALID` in the response. Surface as "GOOGLE_MAPS_API_KEY is invalid or restricted. Check the key in Google Cloud Console."

## Dedupe

- Rows are deduped on `place_id` across paginated `pageToken` responses.

## Out of scope

- Decision-maker enrichment (no names, no titles).
- Personal email lookup.
- LinkedIn scraping.
- Paid enrichment APIs (Apollo, ZoomInfo, Clearbit, etc.).
- CRM writes or push to Salesforce / HubSpot.
- Cross-run dedupe. Each run is independent. The SDR is responsible for merging lists across runs.

## Setup

See `references/places_api_setup.md` for how to enable Places API (New), create a key, and set `GOOGLE_MAPS_API_KEY`.

Install the script's dependencies once:

```
pip install -r scripts/requirements.txt
```

**More from Skills and Agents Co:** see this skill in the [Skills & Agents catalog](https://skillsandagents.co/skills/local-lead-prospector/).
