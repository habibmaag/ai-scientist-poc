# RNA-seq Reproduction Summary

## Paper

**PMID:** 24792119

**Title:** Epigenomic profiling of young and aged HSCs reveals concerted changes during aging that reinforce self-renewal.

## Dataset

**GEO accession:** GSE47817

**Organism:** Mus musculus

**Comparison:** 4-month (young) vs 24-month (aged) HSCs.

## Samples

Young samples: 4

Aged samples: 4

Total samples: 8

## Reproduction Scope

This proof of concept independently reproduces the
young-versus-aged RNA-seq group comparison using
processed, gene-level count data from GEO.

The original publication used:

RUM -> gene-level counting -> DESeq

The PoC does not reimplement DESeq.

Instead, it uses:

1. Library-size normalization
2. Counts per million (CPM)
3. log2(CPM + 1)
4. Welch two-sample t-test
5. Benjamini-Hochberg FDR correction

Significance threshold:

**FDR < 0.05**

## Independent Result

Genes tested: **38,172**

Significant genes: **1,472**

Upregulated in aged HSCs: **921**

Downregulated in aged HSCs: **551**

## Scientific Interpretation

The result is an independent approximation of the published
differential-expression analysis rather than an exact DESeq
reimplementation.

The published DEG table is not used to generate these results.
It is reserved for an independent verification step.

## Limitations

- The original DESeq workflow is not reimplemented.
- The analysis starts from processed gene-level counts.
- The statistical model differs from the publication.
- Parameters are not tuned after observing the published results.

## Next Step

Compare the independently generated result with the published
DEG reference using predefined verification criteria.
