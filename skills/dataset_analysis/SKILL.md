# Dataset Analysis Skill

## Purpose

Identify, retrieve, inspect, and characterize the datasets required
to reproduce a computational analysis described in a scientific paper.

This skill should work across biological data modalities such as:

- RNA-seq
- DNA methylation / WGBS
- ChIP-seq
- proteomics
- single-cell data
- other structured omics datasets

## Inputs

- Structured paper-analysis specification from the Paper Extraction Skill
- Dataset identifiers and repositories identified in the paper

## Workflow

1. Resolve each dataset identifier.
2. Retrieve dataset metadata from the authoritative repository.
3. Confirm that the dataset corresponds to the paper.
4. Identify available files:
   - raw data
   - processed data
   - sample metadata
   - supplementary tables
5. Prefer processed data when it allows the relevant analysis
   to be reproduced within the available computational scope.
6. Inspect file structure, dimensions, columns, identifiers,
   missing values, and data types.
7. Map biological samples to experimental groups.
8. Identify the minimum subset of data required for the
   reproduction workflow.
9. Record all transformations required before analysis.

## Dataset Quality Checks

Before analysis, verify:

- dataset accession matches the paper
- expected number of samples
- expected experimental groups
- expected biological modality
- expected identifiers
- absence of obvious corruption
- appropriate file format
- whether values are raw, normalized, transformed,
  or already statistically summarized

## Sample Metadata

Create an explicit mapping between samples and groups.

Example:

| sample | group |
|---|---|
| sample_1 | young |
| sample_2 | young |
| sample_3 | aged |
| sample_4 | aged |

Do not infer group assignments solely from expression values.

## Modality-Specific Handling

### RNA-seq

Identify whether the available data contain:

- raw counts
- normalized expression
- differential-expression results
- gene annotations

Record the unit and transformation used.

### DNA Methylation / WGBS

Identify whether the available data contain:

- CpG-level methylation
- beta values
- methylation percentages
- genomic coordinates
- gene annotations
- promoter annotations

Record the aggregation strategy if CpG-level data
are converted to gene-level measurements.

## Reproducibility Scope

Select the smallest dataset representation that is sufficient
for the defined reproduction.

For example:

- processed counts instead of raw FASTQ files
- processed methylation tables instead of raw sequencing data

When doing so, explicitly document the deviation from the
original publication pipeline.

## Output

Return a structured dataset specification containing:

- dataset identifier
- source repository
- files used
- sample metadata
- modality
- dimensions
- relevant columns
- preprocessing requirements
- selected subset
- provenance information

## Provenance

Every downloaded dataset must retain:

- source URL
- accession
- original filename
- download date
- any transformation performed

Do not silently modify source data.

## Failure Handling

If a dataset cannot be retrieved:

1. Report the accession and source.
2. Identify the failed file or endpoint.
3. Search for an official alternative representation.
4. Do not substitute an unrelated dataset without explicitly
   documenting the substitution.