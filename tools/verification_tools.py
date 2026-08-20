"""
verification_tools.py

Independent verification of reproduced scientific results.

The verification compares:

    independently generated results
        versus
    published reference results

The verification criteria are defined independently of
the reproduction results.

The LLM is NOT responsible for deciding whether the
reproduction succeeded.
"""

import json
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

FDR_THRESHOLD = 0.05

RESULTS_DIR = Path(
    "results"
)

REPRODUCED_FILENAME = (
    "reproduced_de_results.csv"
)

REFERENCE_PATH = Path(
    "data/cache/GSE47817/"
    "GSE47817_deg.m04_hsc_vs_m24_hsc.txt.gz"
)


# ============================================================
# LOAD RESULTS
# ============================================================

def load_reproduced_results(
    path: Path,
) -> pd.DataFrame:
    """
    Load independently reproduced results.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Reproduced result not found: {path}"
        )

    return pd.read_csv(path)


def load_reference_results(
    path: Path,
) -> pd.DataFrame:
    """
    Load the published DEG reference.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Reference result not found: {path}"
        )

    return pd.read_csv(
        path,
        sep="\t",
        compression="gzip",
    )


# ============================================================
# GENE SET EXTRACTION
# ============================================================

def get_reproduced_gene_sets(
    results: pd.DataFrame,
) -> dict[str, set[str]]:
    """
    Extract significant UP and DN gene sets
    from the independent analysis.
    """

    significant = results[
        results["FDR"] < FDR_THRESHOLD
    ]

    return {
        "UP": set(
            significant.loc[
                significant["log2FC"] > 0,
                "geneSymbol",
            ]
        ),
        "DN": set(
            significant.loc[
                significant["log2FC"] < 0,
                "geneSymbol",
            ]
        ),
    }


def get_reference_gene_sets(
    reference: pd.DataFrame,
) -> dict[str, set[str]]:
    """
    Extract UP and DN gene sets from the published result.
    """

    return {
        "UP": set(
            reference.loc[
                reference["type"] == "UP",
                "geneSymbol",
            ]
        ),
        "DN": set(
            reference.loc[
                reference["type"] == "DN",
                "geneSymbol",
            ]
        ),
    }


# ============================================================
# SET METRICS
# ============================================================

def calculate_set_metrics(
    reproduced: set[str],
    reference: set[str],
) -> dict[str, float | int]:
    """
    Calculate overlap, precision, recall, F1, and Jaccard.
    """

    intersection = reproduced & reference
    union = reproduced | reference

    n_reproduced = len(reproduced)
    n_reference = len(reference)
    n_overlap = len(intersection)

    precision = (
        n_overlap / n_reproduced
        if n_reproduced
        else 0.0
    )

    recall = (
        n_overlap / n_reference
        if n_reference
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall > 0
        else 0.0
    )

    jaccard = (
        n_overlap / len(union)
        if union
        else 0.0
    )

    return {
        "reproduced": n_reproduced,
        "reference": n_reference,
        "overlap": n_overlap,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "jaccard": jaccard,
    }


# ============================================================
# DIRECTION AGREEMENT
# ============================================================

def calculate_direction_agreement(
    reproduced: pd.DataFrame,
    reference: pd.DataFrame,
) -> dict[str, float | int]:
    """
    Compare direction of change among genes significant
    in both analyses.
    """

    reproduced_sig = reproduced[
        reproduced["FDR"] < FDR_THRESHOLD
    ][
        [
            "geneSymbol",
            "log2FC",
        ]
    ].copy()

    reference_sig = reference[
        reference["type"].isin(
            {"UP", "DN"}
        )
    ][
        [
            "geneSymbol",
            "type",
        ]
    ].copy()

    merged = reproduced_sig.merge(
        reference_sig,
        on="geneSymbol",
        how="inner",
    )

    if merged.empty:
        return {
            "overlap_genes": 0,
            "direction_agreement": 0.0,
        }

    merged["reproduced_type"] = "DN"

    merged.loc[
        merged["log2FC"] > 0,
        "reproduced_type",
    ] = "UP"

    agreement = (
        merged["reproduced_type"]
        == merged["type"]
    ).mean()

    return {
        "overlap_genes": len(merged),
        "direction_agreement": float(
            agreement
        ),
    }


# ============================================================
# VERIFICATION STATUS
# ============================================================

def determine_status(
    overall_f1: float,
    direction_agreement: float,
) -> str:
    """
    Apply predefined verification criteria.

    MATCH:
        F1 >= 0.80
        AND direction agreement >= 0.90

    PARTIAL_MATCH:
        F1 >= 0.30
        AND direction agreement >= 0.75

    Otherwise:
        MISMATCH
    """

    if (
        overall_f1 >= 0.80
        and direction_agreement >= 0.90
    ):
        return "MATCH"

    if (
        overall_f1 >= 0.30
        and direction_agreement >= 0.75
    ):
        return "PARTIAL_MATCH"

    return "MISMATCH"


# ============================================================
# FULL VERIFICATION
# ============================================================

def verify_results(
    reproduced_path: Path,
    reference_path: Path,
) -> dict:
    """
    Perform the complete deterministic verification.
    """

    reproduced = load_reproduced_results(
        reproduced_path
    )

    reference = load_reference_results(
        reference_path
    )

    reproduced_sets = get_reproduced_gene_sets(
        reproduced
    )

    reference_sets = get_reference_gene_sets(
        reference
    )

    # --------------------------------------------------------
    # UP genes
    # --------------------------------------------------------

    up_metrics = calculate_set_metrics(
        reproduced_sets["UP"],
        reference_sets["UP"],
    )

    # --------------------------------------------------------
    # DOWN genes
    # --------------------------------------------------------

    down_metrics = calculate_set_metrics(
        reproduced_sets["DN"],
        reference_sets["DN"],
    )

    # --------------------------------------------------------
    # All significant genes
    # --------------------------------------------------------

    reproduced_all = (
        reproduced_sets["UP"]
        | reproduced_sets["DN"]
    )

    reference_all = (
        reference_sets["UP"]
        | reference_sets["DN"]
    )

    overall_metrics = calculate_set_metrics(
        reproduced_all,
        reference_all,
    )

    # --------------------------------------------------------
    # Direction agreement
    # --------------------------------------------------------

    direction = calculate_direction_agreement(
        reproduced,
        reference,
    )

    # --------------------------------------------------------
    # Deterministic status
    # --------------------------------------------------------

    status = determine_status(
        overall_metrics["f1"],
        direction["direction_agreement"],
    )

    return {
        "verification": {
            "status": status,
            "criteria_defined_before_comparison": True,
            "reference_used_to_generate_reproduction": False,
            "post_hoc_parameter_tuning": False,
        },
        "parameters": {
            "fdr_threshold": FDR_THRESHOLD,
            "match_f1_threshold": 0.80,
            "match_direction_threshold": 0.90,
            "partial_match_f1_threshold": 0.30,
            "partial_match_direction_threshold": 0.75,
        },
        "reference": {
            "total_genes": len(reference),
            "upregulated": len(
                reference_sets["UP"]
            ),
            "downregulated": len(
                reference_sets["DN"]
            ),
        },
        "reproduction": {
            "total_genes": len(reproduced),
            "upregulated": len(
                reproduced_sets["UP"]
            ),
            "downregulated": len(
                reproduced_sets["DN"]
            ),
        },
        "comparison": {
            "up": up_metrics,
            "down": down_metrics,
            "overall": overall_metrics,
            "direction": direction,
        },
    }


# ============================================================
# SAVE REPORT
# ============================================================

def save_verification_report(
    report: dict,
    output_path: Path,
) -> None:
    """
    Save the verification report as JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    reproduced_path = (
        RESULTS_DIR
        / REPRODUCED_FILENAME
    )

    report = verify_results(
        reproduced_path,
        REFERENCE_PATH,
    )

    output_path = (
        RESULTS_DIR
        / "verification_report.json"
    )

    save_verification_report(
        report,
        output_path,
    )

    # --------------------------------------------------------
    # Human-readable terminal output
    # --------------------------------------------------------

    print("\nVerification result")
    print("===================")

    print(
        "Status:",
        report["verification"]["status"],
    )

    print("\nUP genes:")
    print(
        report["comparison"]["up"]
    )

    print("\nDOWN genes:")
    print(
        report["comparison"]["down"]
    )

    print("\nOverall:")
    print(
        report["comparison"]["overall"]
    )

    print("\nDirection agreement:")
    print(
        report["comparison"]["direction"]
    )

    print("\nGenerated:")
    print(output_path)