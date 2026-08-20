# AI Scientist PoC — Scientific Paper Reproduction

## Overview

This repository is a proof-of-concept building block for an **AI Scientist** for computational biology.

The system allows a non-technical user to interact with a scientific workflow using natural language. An LLM-based agent can retrieve scientific papers and datasets, extract methods and results from primary-source literature, execute a scoped computational reproduction, and independently verify the reproduced results against published results.

The architecture is designed around:

* LLM-based tool use
* deterministic Python analysis tools
* reusable `SKILL.md` workflow scaffolding
* explicit separation between scientific evidence, computation, and interpretation
* deterministic verification rather than LLM-based self-assessment

The demonstration paper is:

> **Epigenomic profiling of young and aged HSCs reveals concerted changes during aging that reinforce self-renewal.**

PMID: **24792119**

GEO datasets include:

* **GSE47817** — RNA-seq
* **GSE47815** — whole-genome bisulfite sequencing (WGBS)

## Demonstration

The current end-to-end RNA-seq workflow is:

```text
Natural-language request
        ↓
      Claude
        ↓
       tools
        ↓
Paper / dataset discovery
        ↓
GSE47817
        ↓
8 processed RNA-seq samples
        ↓
Independent differential-expression analysis
        ↓
Published-reference verification
        ↓
Claude explains the result
```

Example user request:

```text
Can you reproduce the RNA-seq analysis from PMID 24792119
and tell me whether the results match the paper?
```

The agent retrieves the relevant evidence, executes the analysis, verifies the result, and reports the outcome.

## Repository Structure

```text
ai-scientist-poc/
│
├── README.md
├── requirements.txt
├── .gitignore
├── agent.py
├── reproduce_analysis.py
│
├── data/
│   └── cache/
│       ├── GSE47817/
│       └── papers/
│
├── results/
│   ├── reproduced_de_results.csv
│   ├── reproduction_summary.md
│   └── verification_report.json
│
├── skills/
│   ├── paper_discovery/
│   │   └── SKILL.md
│   ├── paper_extraction/
│   │   └── SKILL.md
│   ├── dataset_analysis/
│   │   └── SKILL.md
│   ├── reproduction/
│   │   └── SKILL.md
│   └── verification/
│       └── SKILL.md
│
└── tools/
    ├── dataset_tools.py
    ├── paper_tools.py
    ├── paper_extraction_tools.py
    ├── reproduction_tools.py
    ├── skill_tools.py
    └── verification_tools.py
```

## Architecture

The architecture separates **workflow reasoning** from **scientific execution**.

```text
                    User
                      │
                      ▼
                  Claude LLM
                      │
              ┌───────┴────────┐
              │                │
          SKILL.md          Tool use
              │                │
              └───────┬────────┘
                      ▼
              Python tools
                      │
       ┌──────────────┼───────────────┐
       ▼              ▼               ▼
   Paper tools    Dataset tools   Analysis tools
       │              │               │
       └──────────────┼───────────────┘
                      ▼
                Verification
                      │
                      ▼
             Evidence + results
                      │
                      ▼
                 Claude answer
```

The LLM does not directly perform the scientific calculations.

Instead:

1. Claude interprets the user's request.
2. Claude selects an appropriate tool.
3. Python executes the deterministic operation.
4. The result is returned to Claude.
5. Claude explains the evidence and result in natural language.

## Skills

The repository contains reusable `SKILL.md` files that provide workflow scaffolding.

### `paper_discovery`

Defines how to identify and retrieve a scientific paper and prioritize authoritative sources.

### `paper_extraction`

Defines how to extract datasets, methods, computational workflows, quantitative results, and reproducible subsets from a paper.

### `dataset_analysis`

Defines how to inspect repository metadata, sample structure, data modality, files, and provenance.

### `reproduction`

Defines how to translate an extracted workflow into an independently executable analysis while documenting deviations from the original publication.

### `verification`

Defines predefined comparison criteria and safeguards against post-hoc modification or self-convincing.

The skills are deliberately generic. The HSC paper is a demonstration case rather than the definition of the architecture.

## RNA-seq Reproduction

### Dataset

The core reproduction uses **GSE47817**, containing eight processed RNA-seq samples:

* four 4-month-old (young) HSC samples
* four 24-month-old (aged) HSC samples

The GEO sample files contain gene-level count and FPKM measurements.

### Original publication workflow

The GEO metadata reports an original workflow based on:

```text
RUM alignment
    ↓
gene-level counting
    ↓
DESeq differential-expression analysis
```

### Independent PoC workflow

The PoC deliberately does not reimplement DESeq.

Instead, it uses:

```text
gene-level counts
    ↓
library-size normalization
    ↓
counts per million (CPM)
    ↓
log2(CPM + 1)
    ↓
Welch two-sample t-test
    ↓
Benjamini-Hochberg FDR
```

The significance threshold is:

```text
FDR < 0.05
```

This is explicitly an **independent approximation**, not an exact reproduction of the publication's statistical model.

### Why this scope was chosen

The assignment is time-boxed and explicitly allows applying the workflow to a limited subpart.

Using processed gene-level counts allows the PoC to demonstrate:

* dataset discovery
* reproducible execution
* scientific verification
* agentic tool use

without attempting to rebuild the complete raw sequencing pipeline.

## Baseline Results

The independent analysis tested:

```text
38,172 genes
```

and identified:

```text
1,472 significant genes
    921 upregulated in aged HSCs
    551 downregulated in aged HSCs
```

The published GEO reference contains:

```text
2,635 differential-expression calls
    1,338 UP
    1,297 DN
```

Comparison of the independently generated result with the published reference produced:

| Metric                                      |    Result |
| ------------------------------------------- | --------: |
| Overall overlap                             | 829 genes |
| Precision                                   |     56.3% |
| Recall                                      |     31.5% |
| F1                                          |     40.4% |
| Jaccard overlap                             |     25.3% |
| Direction agreement among overlapping genes |      100% |

The deterministic verification status is:

```text
PARTIAL_MATCH
```

This is intentionally reported as a **partial match**, not as successful replication.

The key positive finding is that all 829 genes identified as significant by both analyses have the same direction of change.

## Anti-Self-Convincing Design

The verification workflow is explicitly separated from the reproduction workflow.

The published DEG table is:

* not used as input to the independent analysis
* not used to select thresholds
* not used to tune parameters
* used only after the independent result has been generated

Verification is deterministic and based on predefined metrics:

* precision
* recall
* F1
* Jaccard overlap
* direction agreement

The LLM does not determine whether the reproduction is a match.

Instead, Python produces:

```text
MATCH
PARTIAL_MATCH
MISMATCH
```

based on predefined criteria.

A permutation-based negative-control experiment was identified as an important additional validation step, but was intentionally not implemented in the time-boxed PoC.

## Paper Extraction

The agent can retrieve the primary-source full text from NCBI PMC and expose it to Claude.

This allows natural-language questions such as:

```text
What were the main results of PMID 24792119?
```

and:

```text
What analysis workflow did the authors use for the RNA-seq data?
```

to be answered from the actual paper rather than from hard-coded scientific knowledge.

The extraction tool retrieves the structured PMC full text via NCBI EFetch and caches it locally.

## Natural-Language Agent

The agent is started with:

```bash
python agent.py
```

Example:

```text
Ask the AI Scientist: What datasets were used in PMID 24792119?
```

or:

```text
Ask the AI Scientist: What were the main results of PMID 24792119?
```

or:

```text
Ask the AI Scientist: What analysis workflow did the authors use for the RNA-seq data?
```

or:

```text
Ask the AI Scientist: Can you reproduce the RNA-seq analysis from PMID 24792119 and tell me whether the results match the paper?
```

Claude can select and combine tools to answer the request.

## Installation

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set the Anthropic API key:

```bash
export ANTHROPIC_API_KEY="YOUR_API_KEY"
```

An Anthropic model can optionally be selected with:

```bash
export ANTHROPIC_MODEL="claude-sonnet-5"
```

## Running the Components

### Test paper discovery

```bash
python tools/paper_tools.py
```

### Test dataset discovery

```bash
python tools/dataset_tools.py
```

### Test paper extraction

```bash
python tools/paper_extraction_tools.py
```

### Run the RNA-seq reproduction

```bash
python reproduce_analysis.py
```

This generates:

```text
results/reproduced_de_results.csv
results/reproduction_summary.md
```

### Run verification

```bash
python tools/verification_tools.py
```

This generates:

```text
results/verification_report.json
```

### Run the AI Scientist

```bash
python agent.py
```

## Reproducibility

The repository separates:

### Source data

```text
data/cache/
```

Downloaded public datasets and cached paper text are stored here.

### Scientific outputs

```text
results/
```

Generated analysis and verification outputs are stored here.

### Workflow definitions

```text
skills/
```

Reusable scientific workflow instructions are stored here.

### Executable tools

```text
tools/
```

Deterministic retrieval, analysis, extraction, and verification functionality is implemented here.

## Generalisability

The architecture is intentionally not tied to a single paper-specific analysis script.

A new paper should be handled by the same high-level workflow:

```text
paper discovery
      ↓
paper extraction
      ↓
dataset discovery
      ↓
method extraction
      ↓
reproduction
      ↓
verification
```

The current demonstration uses PMID 24792119 because it provides a useful multi-omics computational-biology setting and public datasets suitable for reproduction.

The current dataset association for this specific PMID is explicitly mapped for the PoC. A production implementation would replace this shortcut with fully dynamic accession extraction from the paper and repository metadata.

The same architecture can be extended with additional modality-specific execution tools for:

* RNA-seq
* DNA methylation / WGBS
* ChIP-seq
* single-cell analyses
* survival analysis
* other computational biology workflows

## Multi-omics Extension

A planned extension is to integrate the RNA-seq result with the WGBS dataset:

```text
RNA-seq
   ↓
differential expression
   │
   ├───────────────┐
   │               │
   ▼               ▼
gene ID        promoter /
               gene-body methylation
                   │
                   ▼
            integrated table
```

This extension is intended to demonstrate how the same AI Scientist architecture can move from independent modality-specific analyses toward multi-omics reasoning.

## Limitations

This is a proof of concept rather than a production-ready autonomous scientist.

Important limitations include:

* The RNA-seq statistical model differs from the original DESeq workflow.
* The reproduction begins from processed gene-level counts rather than raw sequencing reads.
* The current dataset association for PMID 24792119 contains a paper-specific shortcut.
* A full negative-control/permutation framework is not yet implemented.
* Multi-omics integration is an extension rather than a complete reproduction of the publication's full epigenomic analysis.
* The LLM is used for workflow orchestration and explanation; deterministic Python tools perform the scientific computations and verification.

## Design Principle

The central design principle is:

> **LLM for orchestration and interpretation; deterministic tools for scientific execution and verification.**

This separation is intended to reduce hallucination, make scientific claims auditable, and allow the workflow to generalize beyond the demonstration paper.
