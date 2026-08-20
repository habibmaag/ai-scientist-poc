# Verification Skill

## Purpose

Independently assess whether reproduced results are consistent with
the results reported in the scientific paper.

The verification process must minimize confirmation bias and prevent
the AI scientist from declaring success based only on qualitative
similarity.

## Inputs

- Paper-analysis specification
- Reference results extracted from the paper
- Reproduction results
- Predefined verification criteria

## Core Principle

Verification criteria must be defined BEFORE inspecting the
reproduction results.

The verification process must be as independent as practical from
the agent that generated the reproduction.

## Workflow

1. Load the reference result extracted from the paper.
2. Load the independently generated reproduction result.
3. Apply predefined comparison metrics.
4. Assess agreement.
5. Run negative or sanity controls where appropriate.
6. Report matches, partial matches, and mismatches.
7. Explain possible causes of disagreement.
8. Never modify the reproduction solely to improve agreement.

## Comparison Types

Depending on the analysis, verification may compare:

- counts of significant features
- overlap between feature sets
- effect directions
- effect sizes
- correlation of statistics
- p-values or adjusted p-values
- performance metrics
- selected biological pathways
- qualitative conclusions

## RNA-seq Example

For differential expression:

- compare the number of significant genes
- calculate overlap between reproduced and reference gene sets
- calculate precision and recall relative to the reference set
- compare direction of effect for overlapping genes
- compare distributions of effect sizes where available

## Multi-omics Example

For RNA-seq and WGBS integration:

- verify that gene identifiers are mapped consistently
- verify expected sample/group structure
- compare direction of methylation and expression changes
- report the number of genes successfully integrated
- distinguish technical mismatches from biological findings

## Negative Controls

Where feasible, perform a control that should not produce the
same signal.

Examples:

- shuffle group labels
- permute sample assignments
- use randomized feature labels

A strong signal under the negative control should be treated as
evidence of a methodological problem.

## Verification Status

Return one of:

### MATCH

The predefined criteria indicate strong agreement.

### PARTIAL_MATCH

Some predefined criteria agree while others do not.

### MISMATCH

The reproduced results do not agree with the reference results
under the predefined criteria.

### UNABLE_TO_VERIFY

There is insufficient information or data to perform the
comparison reliably.

## No Self-Convincing Rule

The verification component must NOT:

- change thresholds after seeing results
- redefine the target result after seeing results
- selectively report only matching metrics
- use an LLM-generated explanation as proof of agreement
- claim replication based only on qualitative similarity

Numerical or explicitly defined comparison criteria should be
used whenever possible.

## Output

Return a structured verification report containing:

- reference result
- reproduced result
- comparison metrics
- predefined thresholds
- negative-control results
- verification status
- discrepancies
- likely explanations
- limitations

## Auditability

All verification calculations should be reproducible from:

- input data
- reference result
- verification parameters
- executable code

The final report must clearly distinguish:

- evidence from the paper
- independently reproduced results
- interpretation