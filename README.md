## Marital Settlement Agreement (MSA) Best Practices Engine

This repo hosts an agentic workflow (designed for Cursor multi-agent) to curate authoritative marriage settlement agreement templates, define a HubSpot-compatible intake schema, generate anonymized mock fact patterns, and run a Markdown-based feedback loop for revision/approval.

### Structure
- `templates/` — curated templates and `manifest.json` metadata
- `intake_schema/` — HubSpot-ready schema (`hubspot_properties.json`, `schema.csv`)
- `mock_data/` — generated anonymized fact patterns (`mock_dataset.json`, `mock_dataset.csv`)
- `scripts/` — utilities for scraping, schema, mock data, feedback, QA
- `feedback/` — revision requests and output
- `context/orchestration/logs/` — feedback engine logs and audit trail
- `logs/` — general logs

### Agents
- Researcher Agent: scrape authoritative templates with Playwright; enrich metadata; normalize best practices.
- Coder Agent: define/export HubSpot schema; implement feedback engine.
- Supervisor Agent: produce ≥50 diverse mock scenarios.
- Reviewer Agent: validate templates, schema coverage, and dataset quality.

### Quick start
1) Generate HubSpot schema (JSON + CSV):
```bash
python3 scripts/schema/generate_schema.py
```
2) Generate mock dataset (50+ scenarios, JSON + CSV):
```bash
python3 scripts/mock/generate_mock_dataset.py --count 50
```

3) Florida MVP — generate MSA drafts (with attachments and clauses):
```bash
# Render two Florida MSAs (with and without children) from mock records
python3 scripts/mock/render_florida_msa.py --index_with_children 0 --index_no_children 1

# Outputs land in drafts/florida/
ls -1 drafts/florida
```

Florida draft details:
- Clause library (auto-injected):
  - templates/clauses/florida/spousal_support/{waived,reserved}.md
  - templates/clauses/florida/property/division.md
  - templates/clauses/florida/child_support/guidelines.md
  - templates/clauses/florida/parenting/plan_ref.md
  - templates/clauses/florida/retirement/qdro.md
- Attachments (auto-appended from mock data):
  - Attachment A — Assets
  - Attachment B — Debts
  - Attachment C — Financial Summary
  - Attachment D — Parenting Plan Summary (when children present)
3) Feedback engine (diff and audit):
```bash
# Create a draft and a revised draft or use request annotations (see below)
python3 scripts/feedback/feedback_engine.py diff \
  --old feedback/samples/draft_v1.md \
  --new feedback/samples/draft_v2.md \
  --out feedback/out

# Or apply simple request annotations to produce a revised draft, then diff
python3 scripts/feedback/feedback_engine.py apply \
  --draft feedback/samples/draft_v1.md \
  --request feedback/requests/request_001.md \
  --out feedback/out
```

### Feedback request annotation syntax (lightweight)
- Replace: `[REPLACE: old text => new text]`
- Append section: `[APPEND: ## Heading | content...]`
- Remove: `[REMOVE: text to remove]`

The engine applies these transforms deterministically, writes a revised draft, emits a Markdown diff, and logs to `context/orchestration/logs/`.

### Scraping templates (Researcher Agent)
- Florida-first focus: prioritize Florida statewide forms (e.g., 12.902, 12.995 series) and guidance pages.
- Configure targets in `scripts/scrape/targets.yaml` and store downloaded sources in `templates/raw/` with `templates/manifest.json` metadata.

### QA validation
```bash
python3 scripts/qa/validate.py
```
Checks:
- ≥20 templates with required metadata
- Intake schema present (JSON + CSV)
- ≥50 mock records
- Feedback engine can produce diffs and logs

### Security and legal
- Mock data only; no PII.
- Public/open-access templates only; cite source URLs in manifest.



### Multi-repo architecture (core + product repos)

To make each drafting template easy to develop in Cursor and deploy to Replit, use a small shared core plus one repo per product.

- **drafter-core (shared)**: helpers for schema validation, manifest utilities, feedback engine, QA checks, and common I/O patterns.
- **Product repos (one per template/jurisdiction)**: e.g., `drafter-florida-msa`, `drafter-texas-msa`. Each contains the product’s templates/clauses and a thin runner (CLI and/or minimal web endpoint) depending on `drafter-core`.

Benefits:
- Faster indexing and snappier Cursor perf per repo
- Independent deploys and secrets in Replit
- Clean versioning and review per product

#### New product quickstart
1) Create a new repo: `drafter-<jurisdiction>-<doc>` (e.g., `drafter-florida-msa`).
2) Add a thin runner:
   - CLI (Python): a `render_*.py` like the Florida example that reads validated intake and writes `drafts/<jurisdiction>/...`.
   - Optional web: minimal FastAPI/Express POST endpoint that returns the rendered draft.
3) Bring product-specific templates/clauses only:
   - `templates/<jurisdiction>/<product>.md`
   - `templates/clauses/<jurisdiction>/**`
4) Depend on `drafter-core` for: schema validation, feedback engine, QA, manifest helpers (once extracted).

#### Replit config (recommended)
Add these files so imports are one-click and environments are pinned.

`.replit`
```ini
run = "bash -lc 'npm i && npx playwright install chromium; python3 scripts/qa/validate.py || true; python3 scripts/mock/render_florida_msa.py --index_with_children 0 --index_no_children 1'"
```

`replit.nix`
```nix
{ pkgs }: {
  deps = [
    pkgs.nodejs_20
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.git
    pkgs.bash
  ];
}
```

Tips:
- Keep `drafts/` gitignored and print the final output path after each run.
- Provide `--offline` to use cached `templates/raw/` and avoid network.
- For Playwright on Replit, install Chromium on boot: `npx playwright install chromium`.

#### Migration plan from this repo
1) Create `drafter-core` and extract shared code:
   - `scripts/feedback/`, `scripts/qa/`, `scripts/schema/`, and cross-cutting utilities.
   - Keep `templates/manifest.json` format and helpers in core.
2) Productize per repo (e.g., `drafter-florida-msa`):
   - Move `templates/florida/**` and relevant `templates/clauses/florida/**`.
   - Provide a `render_florida_msa.py` CLI and optional minimal web endpoint.
3) Wire product repo to `drafter-core` via package (preferred) or git subtree.
4) Add `.replit` and `replit.nix` to each product for one-click runs.

#### CI sanity (per repo)
- Validate schema and manifest: `python3 scripts/qa/validate.py`
- Type-check and dry-run render without network
- Block merges if required metadata is missing

