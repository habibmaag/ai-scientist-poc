# Reproduction Skill

## Purpose

Execute a defined, reproducible subset of a scientific paper's
computational workflow using the public data identified by the
Dataset Analysis Skill.

The goal is not to reproduce every detail of a publication.
The goal is to reproduce a clearly scoped result using an
independent implementation.

## Inputs

- Structured paper-analysis specification
- Dataset specification
- Reproducible analysis scope
- Expected results and evaluation criteria

## Workflow

1. Translate the extracted paper methodology into explicit
   computational steps.
2. Identify which steps can be reproduced with the available data.
3. Document any deviations from the original publication.
4. Implement the workflow in Python.
5. Run the analysis using the specified data.
6. Generate the predefined outputs and metrics.
7. Save intermediate and final results.
8. Pass the results to the Verification Skill.

## Reproduction Principles

### Follow the paper

Use the methodology reported by the paper whenever possible.

Do not silently replace:

- statistical methods
- preprocessing
- thresholds
- normalization
- feature definitions
- evaluation metrics

If a replacement is necessary, document it explicitly.

### Keep the scope explicit

The reproduction must state:

- what part of the paper is reproduced
- what part is not reproduced
- why the scope was chosen

## Independent Implementation

The reproduction code should be independently implemented
from the paper's reported methodology.

Do not use the paper's final reported results as input to
the analysis being reproduced.

Do not modify the analysis after observing results solely
to make them agree with the publication.

## Reproducible Execution

The workflow should be executable from a clean environment.

Record:

- Python version
- package versions
- input datasets
- analysis parameters
- random seeds where applicable

Prefer deterministic execution whenever possible.

## Output

Generate structured results containing:

- analysis name
- input dataset
- sample/group information
- preprocessing performed
- parameters
- generated results
- output file paths
- execution metadata

## HSC RNA-seq Example

For an RNA-seq reproduction, the workflow may include:

1. Load processed expression data.
2. Verify sample metadata.
3. Separate young and aged samples.
4. Apply the predefined differential-expression method.
5. Apply the predefined significance threshold.
6. Generate a list of significant genes.
7. Calculate summary statistics.
8. Compare the reproduced gene set with the
   publication's reported gene set.

## HSC Multi-omics Extension

For the optional WGBS extension:

1. Load processed methylation data.
2. Map methylation measurements to genes or promoters.
3. Calculate predefined methylation differences between groups.
4. Join methylation results with RNA-seq results by gene identifier.
5. Evaluate the relationship between methylation changes
   and expression changes.

The integration must be clearly labeled as an extension when
it is not an exact reproduction of a reported analysis.

## Output Files

Where appropriate, save:

- reproduced differential-expression results
- methylation results
- integrated multi-omics table
- summary metrics
- machine-readable result files

## Failure Handling

If the original workflow cannot be reproduced exactly:

1. Identify the missing component.
2. Determine whether a documented approximation is scientifically reasonable.
3. State the deviation explicitly.
4. Continue only if the resulting analysis remains interpretable.
5. Never present an approximation as an exact reproduction.