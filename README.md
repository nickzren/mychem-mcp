# MyChemInfo MCP Server

A Model Context Protocol (MCP) server that provides access to the [MyChemInfo API](https://mychem.info/), offering comprehensive chemical and drug information from multiple databases including PubChem, ChEMBL, DrugBank, and more.

## Features

### Core Capabilities
- **Chemical Search**: Search by name, formula, InChI, SMILES, CAS, or molecular properties (MW, LogP, HBD/HBA)
- **Drug Information**: Access data from DrugBank, ChEMBL, PubChem, and PharmGKB
- **Structure Operations**: Convert between formats, search by structure, calculate properties
- **Identifier Mapping**: Convert between PubChem CID, ChEMBL ID, DrugBank ID, and 6 other ID types
- **Batch Processing**: Query up to 1000 chemicals in a single request
- **Bioactivity Data**: Search compounds by target activity, compare bioassays across molecules
- **ADMET Properties**: Retrieve absorption, distribution, metabolism, excretion, and toxicity data
- **Clinical Data**: Access clinical trials, FDA approval status, and regulatory information
- **Biological Context**: Explore pathways, disease associations, and mechanisms of action
- **Patent Information**: Search patent data and intellectual property landscape
- **Data Export**: Export results in TSV, CSV, JSON, SDF, or Markdown formats

### Data Sources
- **PubChem**: Chemical structures, properties, bioassays
- **ChEMBL**: Bioactive molecules, drug discovery data
- **DrugBank**: Comprehensive drug information, interactions, targets
- **PharmGKB**: Pharmacogenomics data
- **FDA**: Approval status and label information
- **Patent databases**: Chemical patent information
- **Clinical trials**: Drug development pipeline data

## Quick Start

1. **Install UV**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Setup**
   ```bash
   cd mychem-mcp
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **Configure Claude Desktop**
   ```bash
   python scripts/configure_claude.py
   ```
   Then restart Claude Desktop.

## Usage

#### Running the Server

```bash
mychem-mcp
```

#### Development

```bash
pytest tests/ -v
```
