# Paper Extraction Skill

## Purpose

Read a scientific paper and extract the information required to
understand, reproduce, and verify its computational analyses.

The output should be a structured representation of the paper,
not merely a textual summary.

## Inputs

- Paper metadata from the Paper Discovery Skill
- Full text of the paper when available
- Supplementary material when relevant

## Workflow

1. Identify the scientific question and main objectives.
2. Identify all datasets used in the study.
3. For each dataset, identify:
   - repository
   - accession / identifier
   - organism
   - sample types
   - experimental groups
   - relevant data modality
   - processed or raw data availability
4. Extract the computational analysis workflow.
5. Identify:
   - preprocessing
   - normalization
   - feature selection
   - statistical models
   - thresholds
   - software
   - model parameters
   - evaluation metrics
6. Extract the main quantitative results relevant to the workflow.
7. Identify figures, tables, or supplementary results supporting
   those claims.
8. Identify which parts of the workflow are realistically
   reproducible with the available public data.
9. Convert the reproducible subset into a structured workflow
   specification.

## Analysis Workflow Representation

Represent the workflow as ordered computational steps.

Example:

1. Download processed RNA-seq data.
2. Assign samples to young and aged groups.
3. Perform differential expression analysis.
4. Apply the paper's statistical threshold.
5. Generate significant gene list.
6. Compare reproduced results with the reported results.

## Distinguish Evidence From Interpretation

Clearly separate:

- What the paper explicitly reports.
- What is inferred from the paper.
- What is proposed as a reproduction strategy.

Never present an inferred workflow as an explicit statement
from the authors.

## Result Extraction

For each key result record:

- result description
- numerical value when available
- threshold / definition
- relevant figure or table
- source location
- whether the value will be reproduced

## Reproduction Scope

Identify a clearly defined reproducible subset.

The scope should prioritize:

1. scientifically important results
2. availability of public data
3. computational feasibility
4. reproducibility within the available time

Do not attempt to reproduce the entire paper if a smaller,
well-defined workflow is sufficient.

## Output

Return a structured paper-analysis specification containing:

- scientific question
- datasets
- modalities
- analysis workflow
- methods
- parameters
- key results
- reproducible subset
- expected outputs
- verification criteria
- limitations

## Verification Preparation

For every result selected for reproduction, define in advance:

- what will be calculated independently
- what reference value will be used
- how agreement will be evaluated
- what constitutes a mismatch

The verification criteria must be defined before the reproduction
results are observed.

## Failure Handling

If information cannot be extracted:

1. Identify the missing information.
2. Search supplementary material or authoritative repositories.
3. Mark the field as unknown when necessary.
4. Never invent methods, datasets, parameters, or results.