"""
wgbs_tools.py

WGBS-specific discovery utilities for PMID 24792119.

Current scope:

    GSE47815
        ↓
    discover WGBS samples
        ↓
    identify young / aged samples
        ↓
    download one young + one aged test file
        ↓
    inspect data structure
        ↓
    later: gene-level integration with RNA-seq

The existing RNA-seq backend is intentionally not modified.
"""

from pathlib import Path
from typing import Any

from tools.dataset_tools import (
    download_file,
    inspect_dataset,
    inspect_sample,
)


# ============================================================
# CONFIGURATION
# ============================================================

WGBS_ACCESSION = "GSE47815"

WGBS_DATA_DIR = Path(
    "data/cache/GSE47815"
)


# ============================================================
# DISCOVER WGBS SAMPLES
# ============================================================

def discover_wgbs_samples() -> list[dict[str, Any]]:
    """
    Discover WGBS samples and their processed files.

    Returns
    -------
    list[dict]
        One record per GEO sample.

    Plain English:
        "Find the WGBS samples and ask GEO which processed
        methylation files belong to each sample."
    """

    dataset = inspect_dataset(
        WGBS_ACCESSION
    )

    samples = []

    for sample_id in dataset[
        "sample_ids"
    ]:

        sample = inspect_sample(
            sample_id
        )

        # GEO provides processed WGBS data as BED files.
        processed_files = [
            file
            for file in sample[
                "supplementary_files"
            ]
            if file.endswith(
                ".bed.gz"
            )
        ]

        title = (
            sample.get("title")
            or ""
        ).lower()

        source = (
            sample.get("source_name")
            or ""
        ).lower()

        # ----------------------------------------------------
        # Infer biological group from GEO sample metadata.
        # ----------------------------------------------------

        if (
            "m04" in title
            or "m04" in source
        ):

            age_group = "young"

        elif (
            "m24" in title
            or "m24" in source
        ):

            age_group = "aged"

        else:

            age_group = "unknown"

        samples.append(
            {
                "sample_id": sample_id,
                "title": sample.get(
                    "title"
                ),
                "source_name": sample.get(
                    "source_name"
                ),
                "age_group": age_group,
                "processed_files": processed_files,
                "source_url": sample.get(
                    "source_url"
                ),
            }
        )

    return samples


# ============================================================
# GROUP SAMPLES
# ============================================================

def select_wgbs_samples(
    samples: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Group WGBS samples by biological age.

    Returns
    -------
    dict
        {
            "young": [...],
            "aged": [...]
        }

    Plain English:
        "Separate the samples into young and aged groups."
    """

    selected = {
        "young": [],
        "aged": [],
    }

    for sample in samples:

        group = sample[
            "age_group"
        ]

        if group in selected:

            selected[group].append(
                sample
            )

    return selected


# ============================================================
# DOWNLOAD ONE WGBS SAMPLE
# ============================================================

def download_wgbs_sample(
    sample: dict[str, Any],
) -> Path:
    """
    Download one processed WGBS BED file.

    Parameters
    ----------
    sample:
        Sample record returned by discover_wgbs_samples().

    Returns
    -------
    Path
        Local path to the downloaded file.

    Plain English:
        "Download the processed methylation file for this
        sample."
    """

    files = sample[
        "processed_files"
    ]

    if not files:
        raise ValueError(
            "No processed WGBS BED file found for "
            f"{sample['sample_id']}"
        )

    url = files[0]

    filename = Path(
        url.split("?")[0]
    ).name

    WGBS_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        WGBS_DATA_DIR
        / filename
    )

    return download_file(
        url,
        output_path,
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Discovering WGBS samples from "
        f"{WGBS_ACCESSION}..."
    )

    # --------------------------------------------------------
    # 1. Discover all samples
    # --------------------------------------------------------

    samples = discover_wgbs_samples()

    print(
        f"\nFound {len(samples)} WGBS samples."
    )

    # --------------------------------------------------------
    # 2. Group samples
    # --------------------------------------------------------

    grouped = select_wgbs_samples(
        samples
    )

    print(
        "\nYoung samples:",
        len(grouped["young"]),
    )

    print(
        "Aged samples:",
        len(grouped["aged"]),
    )

    # --------------------------------------------------------
    # 3. Select ONLY one young and one aged sample
    # --------------------------------------------------------

    if not grouped["young"]:
        raise RuntimeError(
            "No young WGBS samples were discovered."
        )

    if not grouped["aged"]:
        raise RuntimeError(
            "No aged WGBS samples were discovered."
        )

    test_samples = [
        grouped["young"][0],
        grouped["aged"][0],
    ]

    print(
        "\nSelected test samples:"
    )

    for sample in test_samples:

        print(
            f" - {sample['sample_id']}: "
            f"{sample['title']} "
            f"({sample['age_group']})"
        )

        for file in sample[
            "processed_files"
        ]:

            print(
                f"     {file}"
            )

    # --------------------------------------------------------
    # 4. Download only those two files
    # --------------------------------------------------------

    print(
        "\nDownloading test WGBS files..."
    )

    downloaded_files = []

    for sample in test_samples:

        path = download_wgbs_sample(
            sample
        )

        downloaded_files.append(
            path
        )

        print(
            "Saved:",
            path
        )

    # --------------------------------------------------------
    # 5. Final output
    # --------------------------------------------------------

    print(
        "\nDownloaded test files:"
    )

    for path in downloaded_files:

        print(
            " -",
            path
        )