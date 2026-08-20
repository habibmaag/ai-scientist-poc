# Multi-omics WGBS / RNA-seq Pilot

## Scope

This is a descriptive multi-omics extension of the
independently reproduced RNA-seq analysis for PMID 24792119.

RNA-seq:

- GEO accession: GSE47817
- 1,472 significant genes
- FDR < 0.05

WGBS:

- GEO accession: GSE47815
- One young sample: GSM1160012
- One aged sample: GSM1160019

## Integration

RNA-seq significant genes were mapped to a simple 2 kb promoter
region using the gene coordinates supplied with the GEO RNA-seq
annotation.

Promoter methylation was summarized as the mean methylation
ratio of overlapping WGBS CpGs.

## Result

RNA-seq genes considered: **1472**

Genes with promoter methylation data: **1470**

Genes without promoter methylation data:
**2**

### Descriptive patterns

| Pattern | Genes |
|---|---:|
| RNA UP / methylation DOWN | 502 |
| RNA UP / methylation UP | 404 |
| RNA DOWN / methylation DOWN | 276 |
| RNA DOWN / methylation UP | 268 |
| Insufficient WGBS data | 22 |

## Interpretation

The pilot demonstrates that an independently generated
transcriptomic result can be linked to a second epigenomic
modality at the gene/promoter level.

The most common observed pattern in this pilot is:
**RNA UP / methylation DOWN**.

However, this should be interpreted as a descriptive pattern
only.

## Important Limitation

Only one young and one aged WGBS sample were used in this pilot.

Therefore:

- no statistical inference is performed;
- no significance is assigned to methylation differences;
- the pilot does not reproduce the full WGBS analysis from the paper;
- the promoter definition is an operational PoC choice.

The purpose is to demonstrate a meaningful multi-omics extension
of the AI Scientist workflow rather than to claim a statistically
validated WGBS reproduction.

## Output

The complete integrated gene-level table is:

`results/multiomics_pilot.csv`
