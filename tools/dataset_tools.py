"""
dataset_tools.py

Tools for discovering, inspecting, and downloading public GEO datasets.

Current demonstration paper:
    PMID 24792119

Current datasets:
    GSE47817 - RNA-seq
    GSE47815 - WGBS

For the current proof of concept, we use GSE47817 RNA-seq.

General workflow:

GEO Series accession
        ↓
Series metadata
        ↓
Sample IDs
        ↓
Sample metadata
        ↓
Processed sample files
        ↓
Local cached data
"""

from pathlib import Path
from typing import Any

import requests


# ============================================================
# GEO
# ============================================================

GEO_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"


# ============================================================
# GEO SERIES
# ============================================================

def inspect_dataset(accession: str) -> dict[str, Any]:
    """
    Retrieve and parse metadata for a GEO Series.

    Parameters
    ----------
    accession:
        GEO accession, e.g. "GSE47817"

    Returns
    -------
    dict
        Structured dataset metadata.

    Plain English:
        "Look up this GEO study and tell me what it contains."
    """

    params = {
        "acc": accession,
        "targ": "self",
        "form": "text",
    }

    response = requests.get(
        GEO_URL,
        params=params,
        timeout=90,
    )

    response.raise_for_status()

    metadata = {}

    for line in response.text.splitlines():

        if not line.startswith("!Series_"):
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        # Some GEO fields occur multiple times,
        # such as sample IDs and supplementary files.
        if key in metadata:

            if not isinstance(metadata[key], list):
                metadata[key] = [metadata[key]]

            metadata[key].append(value)

        else:
            metadata[key] = value

    # --------------------------------------------------------
    # Convert repeated fields into lists
    # --------------------------------------------------------

    sample_ids = metadata.get("!Series_sample_id", [])

    if isinstance(sample_ids, str):
        sample_ids = [sample_ids]

    supplementary_files = metadata.get(
        "!Series_supplementary_file",
        [],
    )

    if isinstance(supplementary_files, str):
        supplementary_files = [supplementary_files]

    return {
        "accession": accession,
        "title": metadata.get("!Series_title"),
        "pmid": metadata.get("!Series_pubmed_id"),
        "modality": metadata.get("!Series_type"),
        "organism": metadata.get("!Series_sample_organism"),
        "platform": metadata.get("!Series_platform_id"),
        "n_samples": len(sample_ids),
        "sample_ids": sample_ids,
        "supplementary_files": supplementary_files,
        "source_url": response.url,
    }


# ============================================================
# GEO SAMPLE
# ============================================================

def inspect_sample(sample_id: str) -> dict[str, Any]:
    """
    Retrieve and parse metadata for one GEO sample.

    Parameters
    ----------
    sample_id:
        GEO sample ID, e.g. "GSM1160029"

    Returns
    -------
    dict
        Structured sample metadata plus the raw GEO record.

    Plain English:
        "Look up this sample and tell me what it contains."
    """

    params = {
        "acc": sample_id,
        "targ": "self",
        "form": "text",
    }

    response = requests.get(
        GEO_URL,
        params=params,
        timeout=90,
    )

    response.raise_for_status()

    metadata = {}

    for line in response.text.splitlines():

        if not line.startswith("!Sample_"):
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if key in metadata:

            if not isinstance(metadata[key], list):
                metadata[key] = [metadata[key]]

            metadata[key].append(value)

        else:
            metadata[key] = value

    # --------------------------------------------------------
    # Extract sample characteristics
    # --------------------------------------------------------

    characteristics = metadata.get(
        "!Sample_characteristics_ch1",
        [],
    )

    if isinstance(characteristics, str):
        characteristics = [characteristics]

    # --------------------------------------------------------
    # Extract data-processing information
    # --------------------------------------------------------

    processing = metadata.get(
        "!Sample_data_processing",
        [],
    )

    if isinstance(processing, str):
        processing = [processing]

    # --------------------------------------------------------
    # Extract source information
    # --------------------------------------------------------

    source_name = metadata.get(
        "!Sample_source_name_ch1"
    )

    # --------------------------------------------------------
    # Extract supplementary files
    #
    # GEO names these fields:
    #
    # !Sample_supplementary_file_1
    # !Sample_supplementary_file_2
    #
    # Therefore we search for any matching key.
    # --------------------------------------------------------

    supplementary_files = []

    for key, value in metadata.items():

        if key.startswith("!Sample_supplementary_file"):

            if isinstance(value, list):
                supplementary_files.extend(value)

            else:
                supplementary_files.append(value)

    return {
        "sample_id": sample_id,
        "title": metadata.get("!Sample_title"),
        "organism": metadata.get("!Sample_organism_ch1"),
        "source_name": source_name,
        "characteristics": characteristics,
        "data_processing": processing,
        "supplementary_files": supplementary_files,
        "source_url": response.url,

        # Keep the original GEO record for auditing/debugging.
        "raw_metadata": response.text,
    }


# ============================================================
# FIND PROCESSED FILES
# ============================================================

def find_processed_files(
    sample: dict[str, Any],
) -> list[str]:
    """
    Return supplementary files associated with a sample.

    Plain English:
        "From this sample's metadata, give me the
        files that are available for download."
    """

    return sample["supplementary_files"]


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download_file(
    url: str,
    output_path: str | Path,
) -> Path:
    """
    Download a file from a URL.

    Parameters
    ----------
    url:
        Remote file URL.

    output_path:
        Local destination.

    Returns
    -------
    Path
        Path to downloaded file.

    Plain English:
        "Download this file and save it locally."
    """

    output_path = Path(output_path)

    # Create destination directory if necessary.
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Don't download a file that already exists.
    if output_path.exists():

        print(f"Already exists: {output_path}")

        return output_path

    # GEO sometimes provides FTP URLs.
    # Convert FTP to HTTPS so requests can handle them.
    if url.startswith("ftp://"):
        url = "https://" + url[len("ftp://"):]

    print(f"Downloading: {url}")

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    output_path.write_bytes(response.content)

    print(f"Saved to: {output_path}")

    return output_path


# ============================================================
# DOWNLOAD ALL PROCESSED SAMPLE FILES
# ============================================================

def download_processed_samples(
    accession: str,
    output_dir: str | Path,
) -> list[Path]:
    """
    Discover and download processed sample files for a GEO Series.

    Parameters
    ----------
    accession:
        GEO Series accession, e.g. "GSE47817"

    output_dir:
        Directory where files should be cached.

    Returns
    -------
    list[Path]
        Paths to downloaded files.

    Plain English:
        "For every sample in this GEO study, find its
        processed TSV and download it if needed."
    """

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # First discover the Series and its samples.
    dataset = inspect_dataset(accession)

    downloaded_files = []

    for sample_id in dataset["sample_ids"]:

        print(f"\nInspecting {sample_id}...")

        # Get metadata for this sample.
        sample = inspect_sample(sample_id)

        # Find all supplementary files.
        files = find_processed_files(sample)

        # For this RNA-seq dataset we want the processed
        # tab-separated .tsv.gz file.
        tsv_files = [
            file
            for file in files
            if file.endswith(".tsv.gz")
        ]

        if not tsv_files:

            print(
                f"No processed TSV found for {sample_id}"
            )

            continue

        # The dataset should provide one processed TSV
        # per sample.
        file_url = tsv_files[0]

        # Extract the original filename from the URL.
        filename = Path(
            file_url.split("?")[0]
        ).name

        output_path = output_dir / filename

        downloaded = download_file(
            file_url,
            output_path,
        )

        downloaded_files.append(downloaded)

    return downloaded_files


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":

    accession = "GSE47817"

    output_dir = Path(
        "data/cache/GSE47817"
    )

    # --------------------------------------------------------
    # Download all processed RNA-seq sample files
    # --------------------------------------------------------

    files = download_processed_samples(
        accession,
        output_dir,
    )

    # --------------------------------------------------------
    # Print final results
    # --------------------------------------------------------

    print("\nDownloaded processed files:")

    for file in files:
        print(" -", file)