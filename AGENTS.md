# Agent Guide — mychem-mcp

Brief for AI coding agents (Claude Code, Codex) working in this repo or routing biomedical questions through it.

## What this server is
MCP server wrapping the [MyChem.info](https://mychem.info/) API. Aggregates chemical/drug annotations from PubChem, ChEMBL, DrugBank, PharmGKB, FDA, patent databases, and clinical trials.

## Run locally (stdio)
```bash
uv sync
uv run python -m mychem_mcp.server               # stdio (default)
```

HTTP/SSE: append `--transport http --host 127.0.0.1 --port 8000`.

## Use this server for
- Chemical / drug lookup by name, formula, InChI, SMILES, CAS, or molecular property (MW, LogP, HBD/HBA)
- Identifier mapping across PubChem CID, ChEMBL ID, DrugBank ID, and 6+ other ID types
- Structure operations: format conversion, structure search, property calculation
- Bioactivity, ADMET, mechanism, target list, indications, side effects
- Clinical / regulatory: clinical-trial pointers, FDA approval status
- Patent landscape and intellectual-property data
- Batch processing (up to 1000 chemicals per request); export to TSV/CSV/JSON/SDF/Markdown

Prefer over other servers when the question is **chemistry-centric** (structure, property, identifier mapping, raw bioactivity) — use opentargets-mcp for **scored drug-target-disease evidence** and pharmacovigilance signals.

## Triage hints
- Identifier mapping ("convert these DrugBank IDs to ChEMBL") → MyChem.
- "Find chemicals with property X in range" → MyChem advanced search.
- For pharmacogenomics, both MyChem and OpenTargets carry PharmGKB-derived data; prefer MyChem for the chemical-anchored view, OpenTargets for the variant/target-anchored view.

## Pitfalls
- Structure searches can be slow; constrain with property filters where possible.
- Some fields are licence-restricted (DrugBank): availability depends on the upstream MyChem deployment.
- Patent and clinical-trial data are pointer-level — follow up at the source for full text.

## Source layout
- `src/mychem_mcp/server.py` — FastMCP entrypoint
- `src/mychem_mcp/client.py` — HTTP client to MyChem.info
- `src/mychem_mcp/tools/` — tool implementations

## Dev
```bash
uv run pytest tests/ -v
```

## When editing tools
1. Add HTTP call in `client.py` if a new endpoint is needed.
2. Wrap in a tool under `src/mychem_mcp/tools/`; expose via the registry.
3. Add a unit test mocking the HTTP response.
