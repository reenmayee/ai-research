# Composio App Research Agent — Case Study

**Live Case Study:** https://reenmayee.github.io/ai-research/

An agentic research pipeline for evaluating 100 applications for AI-agent toolkit buildability, combining Composio toolkit coverage with official documentation research.

## What it does

* Loads the 100-app research set.
* Uses the Composio Python SDK to discover direct and semantic toolkit matches and tool slugs.
* Creates an MCP-enabled Composio session.
* Researches official documentation for authentication, API surface, self-serve/gated access, and MCP availability.
* Captures supporting evidence and confidence for each finding.
* Merges Composio coverage and external research conservatively.
* Classifies apps as `BUILD_NOW`, `BUILD_WITH_CONSTRAINTS`, or `RESEARCH_REQUIRED`.
* Analyzes cross-app patterns and identifies potential toolkit opportunities.
* Flags uncertain records for human verification.
* Generates a self-contained `index.html` case study.

## Pipeline

100 Apps → Composio Coverage + Tool Discovery → Evidence Research → Conservative Merge → Analysis & Prioritization → Human Verification → HTML Case Study

## Run

Install dependencies:

```bash
pip install composio python-dotenv pandas requests beautifulsoup4
```

Create a `.env` file:

```env
COMPOSIO_API_KEY=your_api_key
```

Run from the repository root:

```bash
python project/agent_composio.py
python project/evidence_researcher.py
python project/merge_results.py
python project/analyze_results.py
python project/prototype.py
```

## Outputs

* `index.html` — final case-study page
* `project/data/final_results.json` — merged 100-app dataset
* `project/data/analysis_results.json` — patterns, buildability, and opportunities
* `project/data/composio_results.json` — Composio coverage and tool discovery
* `project/data/research_results.json` — evidence research output
* `project/data/apps.csv` — original research set
* `VERIFICATION.md` — verification and official-document spot checks

## Buildability

The pipeline uses conservative classifications:

* `BUILD_NOW` — documented API, authentication, and self-serve access.
* `BUILD_WITH_CONSTRAINTS` — API/authentication identified, but access is gated or conditional.
* `RESEARCH_REQUIRED` — critical evidence remains uncertain.

Semantic Composio matches are kept separate from confirmed toolkit coverage.

## Verification

Automated research is not treated as ground truth.

The pipeline records evidence, confidence, and human-review requirements. Records with missing or uncertain critical fields are explicitly flagged rather than converted into confident assumptions.

The verification process and spot-check findings are documented in `VERIFICATION.md` and surfaced in the case study.

## Deploy

The final `index.html` is self-contained and requires no backend.

**Live Case Study:** https://reenmayee.github.io/ai-research/

It can be deployed using GitHub Pages.

## Principle

**Automate the research, not the certainty.**
