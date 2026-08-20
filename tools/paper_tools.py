"""
paper_tools.py

Tools for retrieving scientific-paper metadata and
identifying public datasets associated with a paper.

Current demonstration paper:
    PMID 24792119

The architecture is intended to be generalized to other papers.
"""

from typing import Any

import requests


# ============================================================
# PUBMED
# ============================================================

PUBMED_SUMMARY_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
)


def get_paper_metadata(
    pmid: str,
) -> dict[str, Any]:
    """
    Retrieve basic metadata for a paper from PubMed.

    Parameters
    ----------
    pmid:
        PubMed identifier, e.g. "24792119"

    Returns
    -------
    dict
        Structured paper metadata.

    Plain English:
        "Look up this paper in PubMed and give me its
        authoritative bibliographic information."
    """

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "json",
    }

    response = requests.get(
        PUBMED_SUMMARY_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if pmid not in data["result"]:
        raise ValueError(
            f"PubMed record not found for PMID {pmid}"
        )

    result = data["result"][pmid]

    return {
        "pmid": pmid,
        "title": result.get("title"),
        "journal": result.get("fulljournalname"),
        "publication_date": result.get("pubdate"),
        "doi": result.get("elocationid"),
    }


# ============================================================
# PAPER DATASET DISCOVERY
# ============================================================

def get_paper_datasets(
    pmid: str,
) -> list[dict[str, str]]:
    """
    Identify public datasets associated with a paper.

    Parameters
    ----------
    pmid:
        PubMed identifier.

    Returns
    -------
    list[dict]
        Dataset accession, repository, modality,
        and description.

    Plain English:
        "For this paper, which public datasets should
        the scientist consider for reproduction?"

    NOTE:
        For the current PoC, PMID 24792119 is explicitly mapped
        to its verified GEO datasets. This is a temporary
        paper-specific implementation. The architecture is
        designed so this can later be replaced by dynamic
        full-text/accession discovery.
    """

    if pmid == "24792119":

        return [
            {
                "accession": "GSE47817",
                "repository": "NCBI GEO",
                "modality": "RNA-seq",
                "description": (
                    "Transcriptomic profiling of young and "
                    "aged mouse hematopoietic stem cells."
                ),
            },
            {
                "accession": "GSE47815",
                "repository": "NCBI GEO",
                "modality": "WGBS",
                "description": (
                    "Genome-wide DNA methylation profiling of "
                    "young and aged mouse hematopoietic stem cells."
                ),
            },
        ]

    return []


# ============================================================
# SIMPLE LOCAL TEST
# ============================================================

if __name__ == "__main__":

    pmid = "24792119"

    print("Paper metadata:")
    print(
        get_paper_metadata(pmid)
    )

    print("\nAssociated datasets:")

    for dataset in get_paper_datasets(pmid):
        print(dataset)