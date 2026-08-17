# Composio App Research Agent — Case Study

## What it does
- Loads the 100-app research set.
- Uses the Composio Python SDK to discover direct and semantic toolkit matches and tool slugs.
- Creates an MCP-enabled Composio session.
- Fetches official pages and extracts evidence signals for auth, self-serve/gating, API surface and MCP.
- Merges conservatively: semantic matches never count as direct toolkit coverage.
- Produces the standalone `index.html`.

## Run
```bash
pip install composio python-dotenv pandas requests beautifulsoup4
# .env: COMPOSIO_API_KEY=...
python agent_composio.py
python evidence_researcher.py
python merge_results.py
```
Run from the repository root because the scripts use `data/...` paths.

## Outputs
- `index.html` — submission case study
- `data/final_results.json` — merged 100-app dataset
- `data/composio_results.json` — Composio coverage/tool discovery
- `data/apps.csv` — research set
- `VERIFICATION.md` — official-doc spot-check log

## Verification
The first automated pass detected auth signals in 35/100 rows. An 11-app official-doc spot check found 4 auth false negatives: Salesforce, Pipedrive, Shopify and Twilio. The case study shows the misses instead of hiding them.

## Deploy
Deploy the folder as a static site using GitHub Pages, Netlify, or Vercel. No backend is required for the case-study page.
