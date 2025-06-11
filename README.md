# MyChemInfo MCP Server

A Model Context Protocol (MCP) server that provides access to the [MyChemInfo API](https://mychem.info/), offering comprehensive chemical and drug information from multiple databases including PubChem, ChEMBL, DrugBank, and more.

## Features

### Core Capabilities
- **Chemical Search**: Search chemicals by name, formula, InChI, SMILES, or other identifiers
- **Drug Information**: Access data from DrugBank, ChEMBL, PubChem, and PharmGKB
- **Structure Operations**: Convert between formats, search by structure similarity
- **Batch Processing**: Query up to 1000 chemicals in a single request
- **ADMET Properties**: Retrieve absorption, distribution, metabolism, excretion, and toxicity data
- **Clinical Data**: Access clinical trials and FDA approval information
- **Patent Information**: Search patent data for chemicals
- **Data Export**: Export results in TSV, CSV, JSON, or SDF formats

### Data Sources
- **PubChem**: Chemical structures, properties, bioassays
- **ChEMBL**: Bioactive molecules, drug discovery data
- **DrugBank**: Comprehensive drug information, interactions, targets
- **PharmGKB**: Pharmacogenomics data
- **FDA**: Approval status and label information
- **Patent databases**: Chemical patent information
- **Clinical trials**: Drug development pipeline data

## Installation

```bash
git clone https://github.com/nickzren/mychem-mcp
cd mychem-mcp
mamba env create -f environment.yml
mamba activate mychem-mcp
```

## Usage

#### As an MCP Server

```bash
mychem-mcp
```

#### Configure with Claude Desktop

```bash
python scripts/configure_claude.py
```