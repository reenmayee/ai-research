# Composio App Research Agent — Case Study

**Live Case Study:** https://reenmayee.github.io/ai-research/

## What it does

- Loads the 100-app research set.
- Uses the Composio Python SDK to discover direct and semantic toolkit matches and tool slugs.
- Creates an MCP-enabled Composio session.
- Fetches official pages and extracts evidence signals for auth, self-serve/gating, API surface and MCP.
- Merges conservatively: semantic matches never count as direct toolkit coverage.
- Analyzes buildability, patterns and toolkit opportunities.
- Produces the standalone `index.html` case study.

## Run

```bash
pip install composio python-dotenv pandas requests beautifulsoup4

# .env
COMPOSIO_API_KEY=...

python agent_composio.py
python evidence_researcher.py
python merge_results.py
python analyze_results.py
python prototype.py
