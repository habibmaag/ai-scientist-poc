# AI Scientist PoC — Scientific Paper Reproduction and Multi-omics Analysis

## Overview

This repository is a proof-of-concept building block for an **AI Scientist** for computational biology.

The system allows a non-technical stakeholder to interact with a scientific workflow using natural language. An LLM-based agent can:

* identify a scientific paper and its public datasets;
* retrieve and extract information from the primary-source paper;
* inspect public GEO datasets;
* execute a scoped, independent reproduction of a published analysis;
* verify reproduced results against a published reference using deterministic criteria;
* extend the workflow to a second omics modality;
* explain the resulting evidence and limitations in natural language.

The architecture separates **LLM-based orchestration and interpretation** from **deterministic scientific execution and verification**.

## Demonstration Paper

The proof of concept is demonstrated on:

> **Epigenomic profiling of young and aged HSCs reveals concerted changes during aging that reinforce self-renewal.**

**PMID:** 24792119

The study investigates molecular changes associated with aging in highly purified mouse hematopoietic stem cells (HSCs).

Public datasets used in this PoC include:

* **GSE47817** — RNA-seq
* **GSE47815** — whole-genome bisulfite sequencing (WGBS)

The paper also contains histone-modification / ChIP-seq analyses, but these are not reproduced in the current time-boxed PoC.

## End-to-end Concept

A non-technical user can ask a question such as:

```text
Can you reproduce the RNA-seq analysis from PMID 24792119
and tell me whether the results match the paper?
```

The system can then execute:

```text
Natural-language request
        ↓
      Claude
        ↓
   SKILL.md workflows
        ↓
   tool selection
        ↓
┌──────────────┬───────────────┬─────────────────┐
│ Paper tools  │ RNA-seq tools │ Multi-omics     │
│              │               │ WGBS pilot      │
└──────────────┴───────────────┴─────────────────┘
        ↓
deterministic scientific computation
        ↓
verification
        ↓
Claude explanation
```

The LLM does not directly perform the numerical analysis. It orchestrates deterministic Python tools and explains their outputs.

## Repository Structure

```text
ai-scientist-poc/
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── agent.py
├── reproduce_analysis.py
│
├── data/
│   └── cache/
│       ├── GSE47817/
│       ├── GSE47815/
│       └── papers/
│
├── results/
│   ├── reproduced_de_results.csv
│   ├── reproduction_summary.md
│   ├── verification_report.json
│   ├── multiomics_pilot.csv
│   └── multiomics_pilot_summary.md
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
    ├── __init__.py
    ├── dataset_tools.py
    ├── paper_tools.py
    ├── paper_extraction_tools.py
    ├── skill_tools.py
    ├── verification_tools.py
    ├── wgbs_tools.py
    └── multiomics_tools.py
```

## Architecture

The system separates workflow reasoning from scientific execution.

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
        ┌─────────────┼────────────────┐
        ▼             ▼                ▼
    Paper tools    RNA-seq         WGBS /
                   reproduction    multi-omics
        │             │                │
        └─────────────┼────────────────┘
                      ▼
                 Verification
                      │
                      ▼
             Evidence + results
                      │
                      ▼
                Claude answer
```

### Design principle

> **LLM for orchestration and interpretation; deterministic tools for scientific execution and verification.**

This separation is intended to reduce hallucination, keep scientific claims auditable, and make the workflow easier to generalize.

## Skills

The repository contains reusable `SKILL.md` workflow definitions.

### `paper_discovery`

Defines how to identify scientific papers and retrieve authoritative metadata.

### `paper_extraction`

Defines how to extract:

* datasets;
* methods;
* computational workflows;
* quantitative results;
* reproducible analysis subsets.

### `dataset_analysis`

Defines how to inspect public dataset repositories, sample structure, modality, provenance, and available files.

### `reproduction`

Defines how to translate an extracted published workflow into an independently executable analysis while documenting deviations from the original method.

### `verification`

Defines predefined comparison criteria and safeguards against post-hoc tuning and self-convincing.

The skills are deliberately written as reusable workflow scaffolding rather than as instructions specific to one biological system.

## Natural-language Agent

Start the agent with:

```bash
python agent.py
```

Example questions:

```text
What datasets were used in PMID 24792119?
```

```text
What were the main results of PMID 24792119?
```

```text
What analysis workflow did the authors use for the RNA-seq data?
```

```text
Can you reproduce the RNA-seq analysis from PMID 24792119
and tell me whether the results match the paper?
```

```text
Can you integrate the RNA-seq results with the WGBS data
from PMID 24792119?
```

Claude decides which tools are required and can chain multiple tools for a single request.

## Paper Retrieval and Extraction

The agent can retrieve the primary-source article through NCBI/PubMed and PMC.

The extraction tool:

1. resolves the PMID to a PMC identifier;
2. retrieves the full article as structured PMC XML using NCBI EFetch;
3. caches the article locally;
4. extracts the title, abstract, and scientific sections;
5. exposes the resulting text to Claude as primary-source evidence.

This allows questions about methods and results to be answered from the paper itself rather than from hard-coded background knowledge.

## Dataset Discovery

The dataset tools use NCBI GEO metadata to discover:

* GEO Series accessions;
* sample IDs;
* organism;
* modality;
* platform;
* sample characteristics;
* processed files.

The demonstration paper uses:

### GSE47817

RNA-seq profiling of young and aged mouse HSCs.

### GSE47815

Whole-genome bisulfite sequencing profiling of young and aged mouse HSCs.

## RNA-seq Reproduction

### Dataset

The scoped reproduction uses **GSE47817**.

The dataset contains eight processed RNA-seq samples:

* four young / 4-month HSC samples;
* four aged / 24-month HSC samples.

The processed sample files contain gene-level count and FPKM measurements.

### Original publication workflow

The GEO metadata reports the original RNA-seq processing as:

```text
RUM alignment
    ↓
gene-level counting
    ↓
DESeq differential-expression analysis
```

### Independent PoC workflow

The PoC intentionally does **not** attempt to reimplement DESeq.

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

Significance threshold:

```text
FDR < 0.05
```

This is explicitly an **independent approximation**, not an exact replication of the original DESeq statistical model.

### Running the reproduction

```bash
python reproduce_analysis.py
```

Outputs:

```text
results/reproduced_de_results.csv
results/reproduction_summary.md
```

## Baseline RNA-seq Result

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

The published GEO DEG reference contains:

```text
2,635 differential-expression calls
    1,338 UP
    1,297 DN
```

### Verification

The independent result was compared against the published result using predefined metrics.

| Metric                                      | Result |
| ------------------------------------------- | -----: |
| Reproduced significant genes                |  1,472 |
| Published significant genes                 |  2,635 |
| Overall overlap                             |    829 |
| Precision                                   |  56.3% |
| Recall                                      |  31.5% |
| F1                                          |  40.4% |
| Jaccard overlap                             |  25.3% |
| Direction agreement among overlapping genes |   100% |

Verification status:

```text
PARTIAL_MATCH
```

### Interpretation

The independent analysis does not reproduce the complete published DEG set.

However, among the 829 genes called significant by both approaches, the direction of change agrees for **100%** of genes.

The result is therefore best described as:

> **directionally consistent but quantitatively incomplete partial reproduction.**

Differences are expected because the statistical procedures differ substantially:

* original publication: DESeq;
* PoC: log2(CPM + 1) + Welch t-test + Benjamini-Hochberg FDR.

The implementation intentionally does not tune parameters after observing the published reference.

## Anti-Self-Convincing Design

The published DEG table is separated from the independent reproduction.

It is:

* not used as input to the analysis;
* not used to choose thresholds;
* not used to tune parameters;
* only accessed during the verification stage.

Verification is deterministic and based on predefined criteria.

The LLM does not decide whether the reproduction is successful.

Python returns:

```text
MATCH
PARTIAL_MATCH
MISMATCH
```

based on fixed quantitative thresholds.

### Additional validation

A permutation-based negative-control experiment was identified as an important additional safeguard, but was not implemented within the time-boxed PoC.

This is a documented limitation rather than an implicit assumption of validity.

## WGBS and Multi-omics Extension

The paper is intrinsically multi-omics: it combines transcriptomic, DNA-methylation, and histone-modification measurements to investigate HSC aging.

The PoC therefore includes a small **descriptive WGBS integration pilot**.

### WGBS dataset

The pilot uses:

```text
GSE47815
```

The complete dataset contains multiple young and aged WGBS samples.

To keep the proof of concept lightweight, the current pilot uses:

* young: `GSM1160012`
* aged: `GSM1160019`

### Integration workflow

```text
RNA-seq significant genes
        ↓
gene coordinates from GEO RNA-seq annotation
        ↓
simple promoter definition
        ↓
WGBS CpG methylation
        ↓
young vs aged descriptive methylation change
        ↓
integrated gene-level table
```

The operational promoter definition is:

* 2 kb upstream of the transcription start site for plus-strand genes;
* 2 kb downstream of the gene end for minus-strand genes.

### Pilot result

The integration covers:

```text
1,472 RNA-seq significant genes
1,470 with promoter WGBS data
22 without promoter WGBS data
```

Descriptive patterns:

| Pattern                     | Genes |
| --------------------------- | ----: |
| RNA UP / methylation DOWN   |   502 |
| RNA UP / methylation UP     |   404 |
| RNA DOWN / methylation DOWN |   276 |
| RNA DOWN / methylation UP   |   268 |
| Insufficient WGBS data      |    22 |

The most common observed pattern in this pilot is:

> **RNA UP / methylation DOWN**

### Important limitation

This is **not a statistically validated differential-methylation analysis**.

Only one young and one aged WGBS sample are used.

Therefore:

* no inferential p-values are reported;
* no significance is assigned to methylation differences;
* the analysis does not reproduce the full WGBS pipeline used by the paper;
* the promoter definition is an operational PoC choice.

The purpose is to demonstrate how an AI Scientist can extend a scoped transcriptomic reproduction to a second epigenomic modality.

Outputs:

```text
results/multiomics_pilot.csv
results/multiomics_pilot_summary.md
```

## Generalisability

A major design goal is to make the architecture useful beyond the demonstration paper.

The architecture separates:

### Generic workflow capabilities

```text
paper discovery
paper extraction
dataset discovery
verification
LLM orchestration
```

from:

### Modality-specific execution

```text
RNA-seq reproduction
WGBS / multi-omics pilot
future additional modalities
```

This means the same orchestration layer can support other computational-biology papers while plugging in different analysis tools for specific data modalities.

The current demonstration still contains one deliberate PoC shortcut: the paper-to-dataset association for PMID 24792119 is explicitly mapped in `paper_tools.py`.

A production implementation would replace that mapping with fully dynamic extraction of repository accessions from the paper and repository metadata.

The architecture is therefore intended to generalize across papers even though the current scientific execution is demonstrated on one RNA-seq/WGBS case.

## Installation

Create a Python virtual environment:

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

Optionally select a model:

```bash
export ANTHROPIC_MODEL="claude-sonnet-5"
```

## Running the Components

### Paper metadata

```bash
python tools/paper_tools.py
```

### Dataset discovery

```bash
python tools/dataset_tools.py
```

### Paper extraction

```bash
python tools/paper_extraction_tools.py
```

### RNA-seq reproduction

```bash
python reproduce_analysis.py
```

### RNA-seq verification

```bash
python tools/verification_tools.py
```

### WGBS discovery

Because `tools/` is a Python package, run:

```bash
python -m tools.wgbs_tools
```

### Multi-omics pilot

```bash
python -m tools.multiomics_tools
```

### AI Scientist agent

```bash
python agent.py
```

## Generated Scientific Outputs

The repository includes the generated outputs from the demonstrated run:

```text
results/
├── reproduced_de_results.csv
├── reproduction_summary.md
├── verification_report.json
├── multiomics_pilot.csv
└── multiomics_pilot_summary.md
```

These allow a reviewer to inspect the concrete outputs without having to rerun the analysis first.

The downloaded source datasets and paper cache are intentionally excluded from Git because they are external source material that can be downloaded by the tools.

## Reproducibility and Provenance

The repository separates:

### Source data

```text
data/cache/
```

Downloaded public datasets and cached article text.

### Scientific outputs

```text
results/
```

Generated analysis and verification results.

### Workflow definitions

```text
skills/
```

Reusable scientific workflow scaffolding.

### Executable functionality

```text
tools/
```

Deterministic retrieval, extraction, analysis, and verification functions.

### LLM orchestration

```text
agent.py
```

Natural-language interaction and tool selection.

## Limitations

This is a proof of concept rather than a production autonomous scientist.

Important limitations include:

* The RNA-seq statistical model differs from the original DESeq workflow.
* The RNA-seq reproduction begins from processed gene-level counts rather than raw sequencing reads.
* The paper-to-dataset mapping for the demonstration PMID is still partly hard-coded.
* A permutation-based negative control is not yet implemented.
* The WGBS extension is descriptive and uses one young and one aged sample.
* The WGBS integration does not reproduce the paper's complete methylation analysis.
* The current promoter definition is an operational PoC choice.
* The full histone-modification / ChIP-seq component of the paper is not reproduced.
* The LLM is responsible for orchestration and explanation; deterministic Python tools perform scientific computation and verification.

## Future Extensions

Potential next steps include:

1. Fully dynamic extraction of dataset accessions from arbitrary papers.
2. Modality-specific reproduction tools for additional computational-biology workflows.
3. A proper multi-sample WGBS differential-methylation analysis.
4. Integration of the histone-modification / ChIP-seq layer.
5. Automated permutation-based negative controls.
6. Stronger provenance tracking between individual paper claims, datasets, methods, and generated results.
7. More targeted skill loading so only task-relevant `SKILL.md` content is sent to the LLM.

## Summary

This proof of concept demonstrates a small but functional AI Scientist building block:

```text
Natural language
      ↓
LLM reasoning
      ↓
scientific workflow skills
      ↓
tool selection
      ↓
deterministic execution
      ↓
independent verification
      ↓
multi-omics extension
      ↓
natural-language explanation
```

The central design principle is:

> **Use the LLM to orchestrate and explain scientific work, while deterministic tools perform the scientific computation and verification.**
