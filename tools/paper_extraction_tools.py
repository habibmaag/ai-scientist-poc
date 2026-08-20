"""
paper_extraction_tools.py

Tools for retrieving and extracting scientific-paper text.

Workflow:

PMID
  ↓
PubMed
  ↓
PMC ID
  ↓
NCBI PMC EFetch XML
  ↓
download + cache
  ↓
extract article metadata + sections
  ↓
provide primary-source evidence to Claude
"""

from pathlib import Path
from typing import Any
import re
import xml.etree.ElementTree as ET

import requests


# ============================================================
# CONFIGURATION
# ============================================================

PUBMED_FETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/efetch.fcgi"
)

PMC_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/efetch.fcgi"
)

CACHE_DIR = Path(
    "data/cache/papers"
)


# ============================================================
# RESOLVE PMID → PMC ID
# ============================================================

def get_pmc_id(
    pmid: str,
) -> str | None:
    """
    Resolve a PMID to its PMC identifier.

    Plain English:
        "Find the PubMed Central ID corresponding to this paper."
    """

    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml",
    }

    response = requests.get(
        PUBMED_FETCH_URL,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    # Look for:
    #
    # <ArticleId IdType="pmc">PMC4070311</ArticleId>

    match = re.search(
        r'<ArticleId\s+IdType=["\']pmc["\']>'
        r'(PMC\d+)'
        r'</ArticleId>',
        response.text,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


# ============================================================
# DOWNLOAD PMC FULL-TEXT XML
# ============================================================

def download_full_text(
    pmid: str,
) -> Path:
    """
    Download and cache the PMC full-text XML.

    Plain English:
        "Find the PMC article and download its actual
        structured full text."
    """

    pmc_id = get_pmc_id(
        pmid
    )

    if pmc_id is None:
        raise ValueError(
            f"No PMC full text found for PMID {pmid}"
        )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CACHE_DIR
        / f"{pmid}_{pmc_id}.xml"
    )

    # Use cached XML if it already exists.
    if output_path.exists():

        print(
            f"Using cached paper: {output_path}"
        )

        return output_path

    params = {
        "db": "pmc",
        "id": pmc_id,
        "retmode": "xml",
    }

    print(
        f"Downloading PMC full text for {pmc_id}..."
    )

    response = requests.get(
        PMC_EFETCH_URL,
        params=params,
        timeout=120,
    )

    response.raise_for_status()

    # Check that the response looks like XML rather
    # than an HTML error/challenge page.
    content_type = response.headers.get(
        "content-type",
        "",
    ).lower()

    if "html" in content_type:
        raise RuntimeError(
            "NCBI returned HTML instead of PMC XML."
        )

    content_start = response.text.lstrip()

    if not (
        content_start.startswith(
            "<?xml"
        )
        or "<article" in content_start.lower()
    ):
        raise RuntimeError(
            "Downloaded content does not look like PMC XML."
        )

    output_path.write_text(
        response.text,
        encoding="utf-8",
    )

    print(
        f"Saved paper to: {output_path}"
    )

    return output_path


# ============================================================
# XML TEXT EXTRACTION
# ============================================================

def clean_text(
    element: ET.Element,
) -> str:
    """
    Extract readable text recursively from an XML element.

    Plain English:
        "Turn structured XML into normal readable text."
    """

    text = " ".join(
        part.strip()
        for part in element.itertext()
        if part.strip()
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


# ============================================================
# PARSE ARTICLE XML
# ============================================================

def parse_paper(
    xml_path: Path,
) -> dict[str, Any]:
    """
    Parse a PMC article XML file.

    Returns
    -------
    dict
        Article title, abstract, and section-level text.

    Plain English:
        "Read the structured paper and turn its scientific
        content into a Python dictionary."
    """

    xml_text = xml_path.read_text(
        encoding="utf-8"
    )

    root = ET.fromstring(
        xml_text
    )

    # --------------------------------------------------------
    # Main article title
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Use the article's front-matter metadata specifically.
    # This prevents a supplementary-material title from being
    # selected accidentally.

    title_element = root.find(
        ".//front//article-meta//title-group//article-title"
    )

    # Fallback if the XML structure is slightly different.
    if title_element is None:
        title_element = root.find(
            ".//front//article-title"
        )

    title = (
        clean_text(title_element)
        if title_element is not None
        else None
    )

    # --------------------------------------------------------
    # Abstract
    # --------------------------------------------------------

    abstract_elements = root.findall(
        ".//front//abstract"
    )

    abstracts = []

    for abstract in abstract_elements:

        text = clean_text(
            abstract
        )

        if text:
            abstracts.append(
                text
            )

    # Remove duplicate abstracts while preserving order.
    abstract_text = "\n\n".join(
        dict.fromkeys(
            abstracts
        )
    )

    # --------------------------------------------------------
    # Section extraction
    # --------------------------------------------------------

    sections = []

    for section in root.findall(
        ".//sec"
    ):

        title_element = section.find(
            "./title"
        )

        if title_element is None:
            continue

        section_title = clean_text(
            title_element
        )

        # Prefer direct paragraphs in this section.
        paragraphs = section.findall(
            "./p"
        )

        section_parts = []

        for paragraph in paragraphs:

            text = clean_text(
                paragraph
            )

            if text:
                section_parts.append(
                    text
                )

        # Some sections may not use direct <p> children.
        if not section_parts:

            text = clean_text(
                section
            )

            if text:
                section_parts.append(
                    text
                )

        section_text = "\n\n".join(
            section_parts
        )

        if section_text:

            sections.append(
                {
                    "title": section_title,
                    "text": section_text,
                }
            )

    # --------------------------------------------------------
    # Deduplicate exact repeated sections
    # --------------------------------------------------------

    deduplicated_sections = []

    seen = set()

    for section in sections:

        key = (
            section["title"],
            section["text"],
        )

        if key in seen:
            continue

        seen.add(key)

        deduplicated_sections.append(
            section
        )

    return {
        "title": title,
        "abstract": abstract_text,
        "sections": deduplicated_sections,
    }


# ============================================================
# EXTRACT RELEVANT SECTIONS
# ============================================================

def extract_relevant_sections(
    pmid: str,
) -> dict[str, Any]:
    """
    Retrieve the paper and identify sections useful for
    scientific interpretation and reproduction.

    Relevant sections include terms such as:

        Results
        Methods
        Experimental Procedures
        Discussion
        Introduction
        Summary
        Highlights
    """

    xml_path = download_full_text(
        pmid
    )

    paper = parse_paper(
        xml_path
    )

    relevant_keywords = [
        "result",
        "method",
        "experimental",
        "procedure",
        "discussion",
        "introduction",
        "summary",
        "highlight",
    ]

    relevant_sections = []

    for section in paper[
        "sections"
    ]:

        title_lower = (
            section["title"]
            .lower()
        )

        if any(
            keyword in title_lower
            for keyword in relevant_keywords
        ):

            relevant_sections.append(
                section
            )

    return {
        "pmid": pmid,
        "source_file": str(
            xml_path
        ),
        "title": paper[
            "title"
        ],
        "abstract": paper[
            "abstract"
        ],
        "sections": relevant_sections,
    }


# ============================================================
# BUILD PAPER CONTEXT
# ============================================================

def build_paper_context(
    pmid: str,
    max_chars: int = 60000,
) -> str:
    """
    Build a bounded primary-source context for Claude.

    Plain English:
        "Give Claude the scientifically relevant parts of
        the paper while keeping the prompt reasonably sized."
    """

    extracted = (
        extract_relevant_sections(
            pmid
        )
    )

    parts = [
        f"Paper PMID: {pmid}",
        "",
        f"Title: {extracted['title']}",
        "",
    ]

    if extracted["abstract"]:

        parts.append(
            "## Abstract"
        )

        parts.append(
            extracted["abstract"]
        )

        parts.append("")

    current_length = sum(
        len(part)
        for part in parts
    )

    for section in extracted[
        "sections"
    ]:

        formatted = (
            f"## {section['title']}\n\n"
            f"{section['text']}\n\n"
        )

        if (
            current_length
            + len(formatted)
            > max_chars
        ):

            break

        parts.append(
            formatted
        )

        current_length += len(
            formatted
        )

    return "\n".join(
        parts
    )


# ============================================================
# PUBLIC TOOL
# ============================================================

def get_paper_text(
    pmid: str,
) -> dict[str, Any]:
    """
    Retrieve primary-source paper text for the AI Scientist.

    Returns:

        - PMID
        - title
        - source file
        - available section names
        - bounded paper text

    Plain English:
        "Give Claude the actual paper so it can extract
        methods, datasets, results, and workflow from evidence."
    """

    extracted = (
        extract_relevant_sections(
            pmid
        )
    )

    context = build_paper_context(
        pmid
    )

    return {
        "pmid": pmid,
        "title": extracted[
            "title"
        ],
        "source_file": extracted[
            "source_file"
        ],
        "available_sections": [
            section["title"]
            for section in extracted[
                "sections"
            ]
        ],
        "paper_text": context,
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    pmid = "24792119"

    result = get_paper_text(
        pmid
    )

    print(
        "\nPMID:"
    )

    print(
        result["pmid"]
    )

    print(
        "\nTitle:"
    )

    print(
        result["title"]
    )

    print(
        "\nAvailable sections:"
    )

    for section in result[
        "available_sections"
    ]:

        print(
            " -",
            section,
        )

    print(
        "\nSource file:"
    )

    print(
        result["source_file"]
    )

    print(
        "\nPaper text preview:"
    )

    print(
        result["paper_text"][:8000]
    )