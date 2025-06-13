# MyChem MCP Server

A Model Context Protocol (MCP) server that provides access to the [MyChem API](https://mychem.info/).

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

## Prerequisites

- Python 3.12+ with pip

## Quick Start

### 1. Install UV
UV is a fast Python package and project manager.

```bash
pip install uv
```

### 2. Install MCPM (MCP Manager)
MCPM is a package manager for MCP servers that simplifies installation and configuration.

```bash
pip install mcpm
```

### 3. Setup the MCP Server
```bash
cd mychem-mcp
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 4. Add the Server to Claude Desktop
```bash
# Make sure you're in the project directory
cd mychem-mcp

# Set Claude as the target client
mcpm target set @claude-desktop

# Get the full Python path from your virtual environment
# On macOS/Linux:
source .venv/bin/activate
PYTHON_PATH=$(which python)

# On Windows (PowerShell):
# .venv\Scripts\activate
# $PYTHON_PATH = (Get-Command python).Path

# Add the MyChem MCP server
mcpm import stdio mychem \
  --command "$PYTHON_PATH" \
  --args "-m mychem_mcp.server"
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
