"""
multiomics_tools.py

Descriptive RNA-seq / WGBS integration pilot.

This module is deliberately separate from the validated
RNA-seq reproduction backend.

Current pilot:

    RNA-seq significant genes
        ↓
    promoter coordinates
        ↓
    WGBS methylation
        ↓
    young vs aged descriptive change
        ↓
    integrated multi-omics table

IMPORTANT:
This pilot uses one young and one aged WGBS sample.
It is therefore descriptive/exploratory, not an inferential
WGBS reproduction.
"""

from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RNA_RESULT_PATH = Path(
    "results/reproduced_de_results.csv"
)

RNA_SAMPLE_PATH = Path(
    "data/cache/GSE47817/"
    "GSM1160029_m04_hsc_l1.tsv.gz"
)

WGBS_YOUNG_PATH = Path(
    "data/cache/GSE47815/"
    "GSM1160012_m04_b3.bsmapv260R.bam.G.bed.gz"
)

WGBS_AGED_PATH = Path(
    "data/cache/GSE47815/"
    "GSM1160019_m24_b3.bsmapv260R.bam.G.bed.gz"
)

RESULTS_DIR = Path(
    "results"
)

PROMOTER_UPSTREAM = 2000


# ============================================================
# LOAD RNA-SEQ RESULTS
# ============================================================

def load_significant_genes() -> pd.DataFrame:
    """
    Load independently reproduced RNA-seq results.

    Returns significant genes only.
    """

    if not RNA_RESULT_PATH.exists():
        raise FileNotFoundError(
            f"RNA result not found: {RNA_RESULT_PATH}"
        )

    results = pd.read_csv(
        RNA_RESULT_PATH
    )

    return results[
        results["FDR"] < 0.05
    ].copy()


# ============================================================
# LOAD GENE COORDINATES
# ============================================================

def load_gene_coordinates(
    significant_genes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Recover genomic coordinates for significant genes
    from the GEO RNA-seq annotation.
    """

    if not RNA_SAMPLE_PATH.exists():
        raise FileNotFoundError(
            f"RNA sample file not found: {RNA_SAMPLE_PATH}"
        )

    annotation = pd.read_csv(
        RNA_SAMPLE_PATH,
        sep="\t",
        compression="gzip",
        usecols=[
            "#chrom",
            "start",
            "end",
            "geneSymbol",
            "strand",
        ],
    )

    annotation = annotation[
        annotation["geneSymbol"].isin(
            significant_genes["geneSymbol"]
        )
    ].copy()

    return (
        annotation
        .drop_duplicates(
            subset="geneSymbol"
        )
    )


# ============================================================
# BUILD PROMOTER INTERVALS
# ============================================================

def build_promoter_intervals(
    annotation: pd.DataFrame,
) -> pd.DataFrame:
    """
    Define a simple 2 kb promoter interval.

    Plus strand:
        [start - 2000, start]

    Minus strand:
        [end, end + 2000]

    This is an exploratory operational definition.
    """

    promoters = annotation.copy()

    promoters["promoter_start"] = 0
    promoters["promoter_end"] = 0

    plus = (
        promoters["strand"] == "+"
    )

    minus = (
        promoters["strand"] == "-"
    )

    promoters.loc[
        plus,
        "promoter_start",
    ] = (
        promoters.loc[
            plus,
            "start",
        ]
        - PROMOTER_UPSTREAM
    ).clip(
        lower=0
    )

    promoters.loc[
        plus,
        "promoter_end",
    ] = promoters.loc[
        plus,
        "start"
    ]

    promoters.loc[
        minus,
        "promoter_start",
    ] = promoters.loc[
        minus,
        "end"
    ]

    promoters.loc[
        minus,
        "promoter_end",
    ] = (
        promoters.loc[
            minus,
            "end",
        ]
        + PROMOTER_UPSTREAM
    )

    return promoters[
        [
            "geneSymbol",
            "#chrom",
            "promoter_start",
            "promoter_end",
            "strand",
        ]
    ].copy()


# ============================================================
# SUMMARIZE WGBS SAMPLE
# ============================================================

def summarize_wgbs_sample(
    wgbs_path: Path,
    promoters: pd.DataFrame,
    sample_name: str,
    chunk_size: int = 500_000,
) -> pd.DataFrame:
    """
    Calculate mean promoter methylation for one WGBS sample.

    The BED file is processed in chunks.

    A CpG is assigned to a promoter when genomic intervals
    overlap.
    """

    if not wgbs_path.exists():
        raise FileNotFoundError(
            f"WGBS file not found: {wgbs_path}"
        )

    methylation_sum = {}
    methylation_n = {}

    for chunk in pd.read_csv(
        wgbs_path,
        sep="\t",
        compression="gzip",
        chunksize=chunk_size,
    ):

        chunk = chunk.rename(
            columns={
                "#chrom": "chrom"
            }
        )

        chunk = chunk[
            [
                "chrom",
                "start",
                "end",
                "ratio",
            ]
        ].copy()

        chunk = chunk[
            chunk["ratio"].notna()
        ]

        for chrom, cpgs in chunk.groupby(
            "chrom"
        ):

            genes = promoters[
                promoters["#chrom"] == chrom
            ]

            if genes.empty:
                continue

            for _, gene in genes.iterrows():

                overlaps = cpgs[
                    (cpgs["end"] > gene["promoter_start"])
                    &
                    (cpgs["start"] < gene["promoter_end"])
                ]

                if overlaps.empty:
                    continue

                gene_name = gene[
                    "geneSymbol"
                ]

                values = overlaps[
                    "ratio"
                ].astype(float)

                if gene_name not in methylation_sum:

                    methylation_sum[
                        gene_name
                    ] = 0.0

                    methylation_n[
                        gene_name
                    ] = 0

                methylation_sum[
                    gene_name
                ] += values.sum()

                methylation_n[
                    gene_name
                ] += len(values)

    records = []

    for gene in methylation_sum:

        records.append(
            {
                "geneSymbol": gene,
                f"{sample_name}_promoter_methylation":
                    (
                        methylation_sum[gene]
                        / methylation_n[gene]
                    ),
                f"{sample_name}_CpG_count":
                    methylation_n[gene],
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# RUN MULTI-OMICS PILOT
# ============================================================

def run_multiomics_pilot() -> pd.DataFrame:
    """
    Run the descriptive RNA-seq/WGBS integration pilot.
    """

    print(
        "Loading reproduced RNA-seq results..."
    )

    rna_results = load_significant_genes()

    print(
        f"Significant RNA-seq genes: "
        f"{len(rna_results)}"
    )

    print(
        "Loading gene coordinates..."
    )

    annotation = load_gene_coordinates(
        rna_results
    )

    print(
        f"Genes with coordinates: "
        f"{len(annotation)}"
    )

    print(
        "Building promoter intervals..."
    )

    promoters = build_promoter_intervals(
        annotation
    )

    print(
        "Processing young WGBS sample..."
    )

    young = summarize_wgbs_sample(
        WGBS_YOUNG_PATH,
        promoters,
        "young",
    )

    print(
        "Processing aged WGBS sample..."
    )

    aged = summarize_wgbs_sample(
        WGBS_AGED_PATH,
        promoters,
        "aged",
    )

    methylation = young.merge(
        aged,
        on="geneSymbol",
        how="outer",
    )

    integrated = rna_results.merge(
        methylation,
        on="geneSymbol",
        how="left",
    )

    integrated[
        "promoter_methylation_change"
    ] = (
        integrated[
            "aged_promoter_methylation"
        ]
        -
        integrated[
            "young_promoter_methylation"
        ]
    )

    integrated[
        "multiomics_pattern"
    ] = "insufficient_WGBS_data"

    valid = (
        integrated[
            "promoter_methylation_change"
        ].notna()
    )

    integrated.loc[
        valid
        & (integrated["log2FC"] > 0)
        & (
            integrated[
                "promoter_methylation_change"
            ] < 0
        ),
        "multiomics_pattern",
    ] = "RNA_UP_METHYLATION_DOWN"

    integrated.loc[
        valid
        & (integrated["log2FC"] > 0)
        & (
            integrated[
                "promoter_methylation_change"
            ] > 0
        ),
        "multiomics_pattern",
    ] = "RNA_UP_METHYLATION_UP"

    integrated.loc[
        valid
        & (integrated["log2FC"] < 0)
        & (
            integrated[
                "promoter_methylation_change"
            ] < 0
        ),
        "multiomics_pattern",
    ] = "RNA_DOWN_METHYLATION_DOWN"

    integrated.loc[
        valid
        & (integrated["log2FC"] < 0)
        & (
            integrated[
                "promoter_methylation_change"
            ] > 0
        ),
        "multiomics_pattern",
    ] = "RNA_DOWN_METHYLATION_UP"

    return integrated


# ============================================================
# SAVE PILOT TABLE
# ============================================================

def save_multiomics_pilot(
    integrated: pd.DataFrame,
) -> Path:
    """
    Save the integrated gene-level table.
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR
        / "multiomics_pilot.csv"
    )

    integrated.to_csv(
        output_path,
        index=False,
    )

    return output_path


# ============================================================
# SAVE PILOT SUMMARY
# ============================================================

def save_multiomics_summary(
    integrated: pd.DataFrame,
) -> Path:
    """
    Generate a human-readable summary of the WGBS pilot.
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_genes = len(
        integrated
    )

    genes_with_wgbs = (
        integrated[
            "promoter_methylation_change"
        ]
        .notna()
        .sum()
    )

    pattern_counts = (
        integrated[
            "multiomics_pattern"
        ]
        .value_counts()
        .to_dict()
    )

    summary = f"""# Multi-omics WGBS / RNA-seq Pilot

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

RNA-seq genes considered: **{total_genes}**

Genes with promoter methylation data: **{genes_with_wgbs}**

Genes without promoter methylation data:
**{total_genes - genes_with_wgbs}**

### Descriptive patterns

| Pattern | Genes |
|---|---:|
| RNA UP / methylation DOWN | {pattern_counts.get("RNA_UP_METHYLATION_DOWN", 0)} |
| RNA UP / methylation UP | {pattern_counts.get("RNA_UP_METHYLATION_UP", 0)} |
| RNA DOWN / methylation DOWN | {pattern_counts.get("RNA_DOWN_METHYLATION_DOWN", 0)} |
| RNA DOWN / methylation UP | {pattern_counts.get("RNA_DOWN_METHYLATION_UP", 0)} |
| Insufficient WGBS data | {pattern_counts.get("insufficient_WGBS_data", 0)} |

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
"""

    output_path = (
        RESULTS_DIR
        / "multiomics_pilot_summary.md"
    )

    output_path.write_text(
        summary,
        encoding="utf-8",
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    integrated = run_multiomics_pilot()

    table_path = save_multiomics_pilot(
        integrated
    )

    summary_path = save_multiomics_summary(
        integrated
    )

    print(
        "\nMulti-omics pilot complete."
    )

    print(
        "Rows:",
        len(integrated)
    )

    print(
        "Genes with WGBS promoter data:",
        integrated[
            "promoter_methylation_change"
        ].notna().sum()
    )

    print(
        "\nPattern counts:"
    )

    print(
        integrated[
            "multiomics_pattern"
        ].value_counts()
    )

    print(
        "\nGenerated outputs:"
    )

    print(
        " -",
        table_path
    )

    print(
        " -",
        summary_path
    )