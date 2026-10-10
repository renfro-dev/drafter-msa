# Drafter MSA

A prototype engine for drafting Marital Settlement Agreements (MSAs). It curates public court templates, defines a HubSpot-compatible intake schema, generates synthetic fact patterns, renders Florida MSA drafts from them, and runs a markdown-based revision loop.

Built as an agentic workflow for Cursor, with one agent per stage. Florida is the first jurisdiction.

> Not legal advice. All client data in this repository is synthetic, and templates come from public, open-access sources cited in [`templates/manifest.json`](templates/manifest.json).

## What's in the repo

| Path | Contents |
|------|----------|
| `templates/` | Florida MSA templates (with and without children), a clause library, and a manifest of 52 source templates |
| `intake_schema/` | Intake fields as HubSpot properties (`hubspot_properties.json`) and CSV |
| `mock_data/` | 50 synthetic fact patterns in JSON and CSV |
| `scripts/` | Scraping, schema generation, mock data, rendering, feedback, and QA |
| `feedback/` | Sample draft and revision request |

## The agents

- **Researcher:** scrapes authoritative templates with Playwright and records their metadata.
- **Coder:** defines the intake schema and implements the feedback engine.
- **Supervisor:** produces at least 50 varied mock scenarios.
- **Reviewer:** validates templates, schema coverage, and dataset quality.

## Quick start

Requires Python 3 and, for scraping only, Node.js 20+.

```bash
git clone https://github.com/renfro-dev/drafter-msa.git
cd drafter-msa
```

**1. Generate the intake schema**

```bash
python3 scripts/schema/generate_schema.py
```

**2. Generate mock fact patterns**

```bash
python3 scripts/mock/generate_mock_dataset.py --count 50
```

**3. Render Florida MSA drafts**

```bash
python3 scripts/mock/render_florida_msa.py --index_with_children 0 --index_no_children 1
```

Drafts are written to `drafts/florida/`. Each draft pulls clauses from `templates/clauses/florida/` (spousal support, property division, child support, parenting plan, retirement) and appends attachments built from the fact pattern: assets, debts, a financial summary, and a parenting plan summary when children are present.

**4. Validate**

```bash
python3 scripts/qa/validate.py
```

Checks that there are at least 20 templates with required metadata, the intake schema exists, there are at least 50 mock records, and the feedback engine produces diffs and logs.

## Revising a draft

The feedback engine applies simple annotations to a draft, writes the revision, and emits a markdown diff.

```bash
python3 scripts/feedback/feedback_engine.py apply \
  --draft feedback/samples/draft_v1.md \
  --request feedback/requests/request_001.md \
  --out feedback/out
```

| Annotation | Effect |
|------------|--------|
| `[REPLACE: old text => new text]` | Replace text |
| `[APPEND: ## Heading \| content...]` | Add a section |
| `[REMOVE: text to remove]` | Delete text |

To compare two existing drafts, use `feedback_engine.py diff --old <file> --new <file> --out <dir>`.

## Scraping templates

Targets are listed in [`scripts/scrape/targets.yaml`](scripts/scrape/targets.yaml), with Florida statewide family law forms first.

```bash
npm install
npx playwright install chromium
npm run scrape:targets
```

## Status

Prototype. A related, more complete project is [drafter-prenups](https://github.com/renfro-dev/drafter-prenups), a web app that generates California prenuptial agreements.
