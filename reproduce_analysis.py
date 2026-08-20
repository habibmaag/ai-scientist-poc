"""
reproduce_analysis.py

Independent reproduction of a defined RNA-seq analysis
from PMID 24792119.

Paper:
    Epigenomic profiling of young and aged HSCs reveals
    concerted changes during aging that reinforce self-renewal.

Dataset:
    GSE47817

Current reproduction scope:
    Young (4-month) vs aged (24-month) HSC RNA-seq.

Original publication:
    RUM -> gene-level counting -> DESeq

Independent proof-of-concept implementation:
    gene counts
        ↓
    library-size normalization
        ↓
    counts per million (CPM)
        ↓
    log2(CPM + 1)
        ↓
    Welch t-test
        ↓
    Benjamini-Hochberg FDR

The published DEG table is used ONLY as a later
verification reference.

This module can be:

    1. Run directly from the command line:
           python reproduce_analysis.py

    2. Imported by the AI Scientist agent:
           from reproduce_analysis import run_reproduction
"""


from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import false_discovery_control
from scipy.stats import ttest_ind


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = Path(
    "data/cache/GSE47817"
)

RESULTS_DIR = Path(
    "results"
)

FDR_THRESHOLD = 0.05


# ============================================================
# FIND SAMPLE FILES
# ============================================================

def get_sample_files(
    data_dir: Path,
) -> list[Path]:
    """
    Find all processed RNA-seq sample files.

    Plain English:
        "Find all downloaded sample-level RNA-seq files."
    """

    return sorted(
        data_dir.glob("GSM*.tsv.gz")
    )


# ============================================================
# LOAD ONE SAMPLE
# ============================================================

def load_sample(
    file_path: Path,
) -> pd.DataFrame:
    """
    Load one processed GEO RNA-seq sample.

    The GEO files contain multiple columns.
    For this reproduction we only need:

        geneSymbol
        gene-level counts
    """

    df = pd.read_csv(
        file_path,
        sep="\t",
        compression="gzip",
    )

    # Automatically identify the count column.
    #
    # Example:
    #     m04_hsc_l1.ct

    count_columns = [
        column
        for column in df.columns
        if column.endswith(".ct")
    ]

    if len(count_columns) != 1:
        raise ValueError(
            f"Expected exactly one count column in "
            f"{file_path.name}; found {count_columns}"
        )

    count_column = count_columns[0]

    # Keep the gene identifier and count.
    result = df[
        [
            "geneSymbol",
            count_column,
        ]
    ].copy()

    # Use the filename as the sample identifier.
    sample_name = file_path.name.replace(
        ".tsv.gz",
        "",
    )

    # Rename the count column to the sample name.
    result = result.rename(
        columns={
            count_column: sample_name
        }
    )

    return result


# ============================================================
# BUILD COUNT MATRIX
# ============================================================

def build_count_matrix(
    files: list[Path],
) -> pd.DataFrame:
    """
    Build a gene × sample count matrix.

    Plain English:
        "Combine all eight individual sample tables using
        geneSymbol as the common key."
    """

    if not files:
        raise FileNotFoundError(
            "No processed RNA-seq sample files found."
        )

    matrix = None

    for file_path in files:

        sample = load_sample(
            file_path
        )

        if matrix is None:

            # First sample becomes the starting matrix.
            matrix = sample

        else:

            # Add each additional sample by geneSymbol.
            matrix = matrix.merge(
                sample,
                on="geneSymbol",
                how="outer",
            )

    # --------------------------------------------------------
    # Convert all sample columns to numeric values.
    # --------------------------------------------------------

    sample_columns = [
        column
        for column in matrix.columns
        if column != "geneSymbol"
    ]

    matrix[sample_columns] = (
        matrix[sample_columns]
        .fillna(0)
        .astype(float)
    )

    return matrix


# ============================================================
# ASSIGN EXPERIMENTAL GROUPS
# ============================================================

def get_sample_groups(
    matrix: pd.DataFrame,
) -> dict[str, str]:
    """
    Assign samples to young or aged groups.

    GEO filenames encode age:

        m04 -> young
        m24 -> aged

    Plain English:
        "Determine which biological group each sample belongs to."
    """

    groups = {}

    for column in matrix.columns:

        # Skip the gene identifier column.
        if column == "geneSymbol":
            continue

        if "_m04_" in column:

            groups[column] = "young"

        elif "_m24_" in column:

            groups[column] = "aged"

        else:

            raise ValueError(
                f"Could not determine experimental group "
                f"from sample name: {column}"
            )

    return groups


# ============================================================
# NORMALIZE COUNTS
# ============================================================

def normalize_counts(
    counts: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert raw counts to log2(CPM + 1).

    Steps:

        1. Calculate total library size for each sample.
        2. Convert counts to counts per million (CPM).
        3. Apply log2(CPM + 1).

    Plain English:
        "Adjust for differences in sequencing depth between
        samples, then transform the values for comparison."
    """

    sample_columns = [
        column
        for column in counts.columns
        if column != "geneSymbol"
    ]

    # Total number of counts in each sample.
    library_sizes = counts[
        sample_columns
    ].sum(axis=0)

    # Convert to counts per million.
    cpm = (
        counts[sample_columns]
        .div(
            library_sizes,
            axis=1,
        )
        * 1_000_000
    )

    # Log transform with a pseudocount.
    log_cpm = np.log2(
        cpm + 1
    )

    result = counts[
        ["geneSymbol"]
    ].copy()

    result[sample_columns] = log_cpm

    return result


# ============================================================
# DIFFERENTIAL EXPRESSION
# ============================================================

def run_differential_expression(
    normalized: pd.DataFrame,
    groups: dict[str, str],
) -> pd.DataFrame:
    """
    Perform the independent young-vs-aged differential-expression
    analysis.

    Statistical method:

        Welch's two-sample t-test

    Multiple-testing correction:

        Benjamini-Hochberg FDR

    Definition of log2FC:

        mean(aged) - mean(young)

    Therefore:

        positive log2FC -> higher in aged HSCs
        negative log2FC -> lower in aged HSCs

    Plain English:
        "For each gene, compare expression between young and
        aged samples and correct the resulting p-values for
        multiple testing."
    """

    # --------------------------------------------------------
    # Identify samples in each biological group.
    # --------------------------------------------------------

    young_samples = [
        sample
        for sample, group in groups.items()
        if group == "young"
    ]

    aged_samples = [
        sample
        for sample, group in groups.items()
        if group == "aged"
    ]

    if not young_samples or not aged_samples:
        raise ValueError(
            "Both young and aged groups are required."
        )

    results = []

    # --------------------------------------------------------
    # Run one statistical test per gene.
    # --------------------------------------------------------

    for _, row in normalized.iterrows():

        gene = row["geneSymbol"]

        young_values = row[
            young_samples
        ].to_numpy(
            dtype=float
        )

        aged_values = row[
            aged_samples
        ].to_numpy(
            dtype=float
        )

        # Effect size:
        # mean expression in aged minus mean expression
        # in young.

        log2fc = (
            np.mean(aged_values)
            - np.mean(young_values)
        )

        # Welch's two-sample t-test.
        _, p_value = ttest_ind(
            aged_values,
            young_values,
            equal_var=False,
            nan_policy="omit",
        )

        results.append(
            {
                "geneSymbol": gene,
                "log2FC": log2fc,
                "p_value": p_value,
            }
        )

    results = pd.DataFrame(
        results
    )

    # --------------------------------------------------------
    # Correct for multiple testing.
    # --------------------------------------------------------

    results["FDR"] = false_discovery_control(
        results["p_value"]
        .fillna(1.0)
        .to_numpy(),
        method="bh",
    )

    # --------------------------------------------------------
    # Classify significant genes.
    # --------------------------------------------------------

    # Start with all genes as non-significant.
    results["type"] = "NS"

    significant = (
        results["FDR"] < FDR_THRESHOLD
    )

    # Higher expression in aged HSCs.
    results.loc[
        significant
        & (results["log2FC"] > 0),
        "type",
    ] = "UP"

    # Lower expression in aged HSCs.
    results.loc[
        significant
        & (results["log2FC"] < 0),
        "type",
    ] = "DN"

    # Most significant genes first.
    results = (
        results
        .sort_values("FDR")
        .reset_index(drop=True)
    )

    return results


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results: pd.DataFrame,
) -> Path:
    """
    Save the complete independent result table.

    Output:
        results/reproduced_de_results.csv

    Plain English:
        "Save all gene-level results so the reproduction
        can be inspected and reused."
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RESULTS_DIR
        / "reproduced_de_results.csv"
    )

    results.to_csv(
        output_path,
        index=False,
    )

    return output_path


def write_reproduction_summary(
    results: pd.DataFrame,
    groups: dict[str, str],
) -> Path:
    """
    Generate a human-readable reproduction summary.

    Output:
        results/reproduction_summary.md
    """

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    significant = results[
        results["FDR"] < FDR_THRESHOLD
    ]

    up = significant[
        significant["log2FC"] > 0
    ]

    down = significant[
        significant["log2FC"] < 0
    ]

    young = [
        sample
        for sample, group in groups.items()
        if group == "young"
    ]

    aged = [
        sample
        for sample, group in groups.items()
        if group == "aged"
    ]

    summary = f"""# RNA-seq Reproduction Summary

## Paper

**PMID:** 24792119

**Title:** Epigenomic profiling of young and aged HSCs reveals concerted changes during aging that reinforce self-renewal.

## Dataset

**GEO accession:** GSE47817

**Organism:** Mus musculus

**Comparison:** 4-month (young) vs 24-month (aged) HSCs.

## Samples

Young samples: {len(young)}

Aged samples: {len(aged)}

Total samples: {len(groups)}

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

**FDR < {FDR_THRESHOLD}**

## Independent Result

Genes tested: **{len(results):,}**

Significant genes: **{len(significant):,}**

Upregulated in aged HSCs: **{len(up):,}**

Downregulated in aged HSCs: **{len(down):,}**

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
"""

    summary_path = (
        RESULTS_DIR
        / "reproduction_summary.md"
    )

    summary_path.write_text(
        summary,
        encoding="utf-8",
    )

    return summary_path


# ============================================================
# RUN COMPLETE REPRODUCTION
# ============================================================

def run_reproduction() -> dict:
    """
    Run the complete scoped RNA-seq reproduction.

    This function is the interface used by the AI Scientist agent.

    Returns
    -------
    dict
        Structured summary of the reproduction.

    Plain English:

        "Run the complete scientific analysis and return
        a compact result that Claude can understand and explain."
    """

    print(
        "[Reproduction] "
        "Looking for processed RNA-seq files..."
    )

    # --------------------------------------------------------
    # 1. Find sample files
    # --------------------------------------------------------

    files = get_sample_files(
        DATA_DIR
    )

    if len(files) != 8:
        raise ValueError(
            "Expected exactly 8 processed RNA-seq "
            f"sample files, found {len(files)}"
        )

    print(
        f"[Reproduction] Found {len(files)} sample files."
    )

    # --------------------------------------------------------
    # 2. Build count matrix
    # --------------------------------------------------------

    counts = build_count_matrix(
        files
    )

    print(
        f"[Reproduction] Count matrix: "
        f"{counts.shape[0]} genes × "
        f"{counts.shape[1] - 1} samples"
    )

    # --------------------------------------------------------
    # 3. Assign biological groups
    # --------------------------------------------------------

    groups = get_sample_groups(
        counts
    )

    # --------------------------------------------------------
    # 4. Normalize
    # --------------------------------------------------------

    print(
        "[Reproduction] Normalizing counts..."
    )

    normalized = normalize_counts(
        counts
    )

    # --------------------------------------------------------
    # 5. Run differential expression
    # --------------------------------------------------------

    print(
        "[Reproduction] Running "
        "differential-expression analysis..."
    )

    results = run_differential_expression(
        normalized,
        groups,
    )

    # --------------------------------------------------------
    # 6. Calculate summary statistics
    # --------------------------------------------------------

    significant = results[
        results["FDR"] < FDR_THRESHOLD
    ]

    up = significant[
        significant["log2FC"] > 0
    ]

    down = significant[
        significant["log2FC"] < 0
    ]

    # --------------------------------------------------------
    # 7. Save outputs
    # --------------------------------------------------------

    csv_path = save_results(
        results
    )

    summary_path = write_reproduction_summary(
        results,
        groups,
    )

    # --------------------------------------------------------
    # 8. Return a compact structured result
    # --------------------------------------------------------

    return {
        "status": "completed",
        "paper_pmid": "24792119",
        "dataset": "GSE47817",
        "analysis": (
            "Young vs aged HSC RNA-seq "
            "differential-expression analysis"
        ),
        "method": (
            "log2(CPM + 1) + Welch t-test + "
            "Benjamini-Hochberg FDR"
        ),
        "fdr_threshold": FDR_THRESHOLD,
        "sample_count": len(groups),
        "genes_tested": len(results),
        "significant_genes": len(significant),
        "upregulated": len(up),
        "downregulated": len(down),
        "result_file": str(csv_path),
        "summary_file": str(summary_path),
    }


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    # Run the same function that the AI Scientist agent uses.

    result = run_reproduction()

    print(
        "\nIndependent analysis summary"
    )
    print(
        "--------------------------------"
    )

    print(
        "Genes tested:",
        result["genes_tested"],
    )

    print(
        f"FDR < {result['fdr_threshold']}:",
        result["significant_genes"],
    )

    print(
        "UP in aged:",
        result["upregulated"],
    )

    print(
        "DOWN in aged:",
        result["downregulated"],
    )

    print(
        "\nGenerated outputs:"
    )

    print(
        " -",
        result["result_file"],
    )

    print(
        " -",
        result["summary_file"],
    )