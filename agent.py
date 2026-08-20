"""
agent.py

LLM-based AI Scientist proof of concept.

The agent can:

1. Receive a natural-language scientific question.
2. Load SKILL.md workflow instructions.
3. Retrieve scientific papers and datasets.
4. Extract primary-source paper text.
5. Run the scoped RNA-seq reproduction.
6. Verify reproduced results against the publication.
7. Return a natural-language answer grounded in tool outputs.

Current tools:

    - get_paper_metadata
    - get_paper_datasets
    - get_paper_text
    - inspect_dataset
    - run_rna_seq_reproduction
    - verify_rna_seq_reproduction

Architecture:

Natural-language user
        ↓
      Claude
        ↓
   workflow skills
        ↓
   tool selection
        ↓
deterministic Python tool
        ↓
      evidence
        ↓
      Claude
        ↓
natural-language answer
"""

import json
import os
from pathlib import Path
from typing import Any

import anthropic

from reproduce_analysis import run_reproduction

from tools.dataset_tools import (
    inspect_dataset,
)

from tools.paper_extraction_tools import (
    get_paper_text,
)

from tools.paper_tools import (
    get_paper_datasets,
    get_paper_metadata,
)

from tools.skill_tools import (
    build_skill_context,
)

from tools.verification_tools import (
    verify_results,
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = os.getenv(
    "ANTHROPIC_MODEL",
    "claude-sonnet-5",
)

MAX_TOKENS = 3000


# ============================================================
# VERIFICATION PATHS
# ============================================================

REPRODUCED_RESULTS = Path(
    "results/reproduced_de_results.csv"
)

REFERENCE_RESULTS = Path(
    "data/cache/GSE47817/"
    "GSE47817_deg.m04_hsc_vs_m24_hsc.txt.gz"
)


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [

    # --------------------------------------------------------
    # 1. PAPER METADATA
    # --------------------------------------------------------

    {
        "name": "get_paper_metadata",

        "description": (
            "Retrieve authoritative PubMed metadata for a "
            "scientific paper using its PMID."
        ),

        "input_schema": {
            "type": "object",

            "properties": {
                "pmid": {
                    "type": "string",
                    "description": (
                        "PubMed identifier, for example "
                        "'24792119'."
                    ),
                }
            },

            "required": [
                "pmid"
            ],
        },
    },

    # --------------------------------------------------------
    # 2. PAPER DATASETS
    # --------------------------------------------------------

    {
        "name": "get_paper_datasets",

        "description": (
            "Identify public datasets associated with a "
            "scientific paper. Returns accessions, repositories, "
            "modalities, and descriptions."
        ),

        "input_schema": {
            "type": "object",

            "properties": {
                "pmid": {
                    "type": "string",
                    "description": (
                        "PubMed identifier, for example "
                        "'24792119'."
                    ),
                }
            },

            "required": [
                "pmid"
            ],
        },
    },

    # --------------------------------------------------------
    # 3. PRIMARY-SOURCE PAPER TEXT
    # --------------------------------------------------------

    {
        "name": "get_paper_text",

        "description": (
            "Retrieve the primary-source full text of a "
            "scientific paper from NCBI PMC. Use this tool "
            "to answer questions about the paper's methods, "
            "analysis workflow, datasets, and main results. "
            "The returned text comes from the article itself."
        ),

        "input_schema": {
            "type": "object",

            "properties": {
                "pmid": {
                    "type": "string",
                    "description": (
                        "PubMed identifier, for example "
                        "'24792119'."
                    ),
                }
            },

            "required": [
                "pmid"
            ],
        },
    },

    # --------------------------------------------------------
    # 4. GEO DATASET INSPECTION
    # --------------------------------------------------------

    {
        "name": "inspect_dataset",

        "description": (
            "Inspect a GEO Series dataset and retrieve "
            "metadata, sample IDs, organism, modality, "
            "platform, and supplementary files."
        ),

        "input_schema": {
            "type": "object",

            "properties": {
                "accession": {
                    "type": "string",
                    "description": (
                        "GEO Series accession, for example "
                        "'GSE47817'."
                    ),
                }
            },

            "required": [
                "accession"
            ],
        },
    },

    # --------------------------------------------------------
    # 5. RNA-SEQ REPRODUCTION
    # --------------------------------------------------------

    {
        "name": "run_rna_seq_reproduction",

        "description": (
            "Run the scoped independent RNA-seq reproduction "
            "for PMID 24792119 using GSE47817. The workflow "
            "uses processed gene-level counts, library-size "
            "normalization, log2(CPM + 1), Welch's t-test, "
            "and Benjamini-Hochberg FDR correction. "
            "Returns summary statistics and generated files."
        ),

        "input_schema": {
            "type": "object",

            "properties": {},

            "required": [],
        },
    },

    # --------------------------------------------------------
    # 6. RNA-SEQ VERIFICATION
    # --------------------------------------------------------

    {
        "name": "verify_rna_seq_reproduction",

        "description": (
            "Compare the independently reproduced RNA-seq "
            "results with the published GSE47817 DEG reference "
            "using predefined deterministic metrics. Returns "
            "precision, recall, F1, Jaccard overlap, direction "
            "agreement, and MATCH/PARTIAL_MATCH/MISMATCH."
        ),

        "input_schema": {
            "type": "object",

            "properties": {},

            "required": [],
        },
    },
]


# ============================================================
# TOOL EXECUTION
# ============================================================

def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
) -> Any:
    """
    Execute a tool selected by Claude.

    Plain English:
        "Claude chooses an action; Python performs it."
    """

    # --------------------------------------------------------
    # Paper metadata
    # --------------------------------------------------------

    if tool_name == "get_paper_metadata":

        return get_paper_metadata(
            tool_input["pmid"]
        )

    # --------------------------------------------------------
    # Paper datasets
    # --------------------------------------------------------

    if tool_name == "get_paper_datasets":

        return {
            "pmid": tool_input["pmid"],
            "datasets": get_paper_datasets(
                tool_input["pmid"]
            ),
        }

    # --------------------------------------------------------
    # Primary-source paper text
    # --------------------------------------------------------

    if tool_name == "get_paper_text":

        return get_paper_text(
            tool_input["pmid"]
        )

    # --------------------------------------------------------
    # GEO dataset inspection
    # --------------------------------------------------------

    if tool_name == "inspect_dataset":

        return inspect_dataset(
            tool_input["accession"]
        )

    # --------------------------------------------------------
    # RNA-seq reproduction
    # --------------------------------------------------------

    if tool_name == "run_rna_seq_reproduction":

        return run_reproduction()

    # --------------------------------------------------------
    # RNA-seq verification
    # --------------------------------------------------------

    if tool_name == "verify_rna_seq_reproduction":

        return verify_results(
            reproduced_path=REPRODUCED_RESULTS,
            reference_path=REFERENCE_RESULTS,
        )

    # --------------------------------------------------------
    # Unknown tool
    # --------------------------------------------------------

    raise ValueError(
        f"Unknown tool requested: {tool_name}"
    )


# ============================================================
# ANTHROPIC CLIENT
# ============================================================

def create_client() -> anthropic.Anthropic:
    """
    Create the Anthropic API client.

    The API key is read from:

        ANTHROPIC_API_KEY
    """

    if not os.getenv(
        "ANTHROPIC_API_KEY"
    ):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set."
        )

    return anthropic.Anthropic()


# ============================================================
# AI SCIENTIST AGENT
# ============================================================

def ask_agent(
    question: str,
) -> str:
    """
    Send a natural-language request to the AI Scientist.

    Claude can decide which tools are needed and in what order.
    """

    client = create_client()

    # --------------------------------------------------------
    # Load workflow skills.
    # --------------------------------------------------------

    skill_context = build_skill_context(
        [
            "paper_discovery",
            "paper_extraction",
            "dataset_analysis",
            "reproduction",
            "verification",
        ]
    )

    # --------------------------------------------------------
    # Conversation state.
    # --------------------------------------------------------

    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]

    # --------------------------------------------------------
    # System instructions.
    # --------------------------------------------------------

    system_prompt = f"""
You are a scientific AI assistant for computational biology
and drug discovery.

Your role is to help non-technical stakeholders interact with
scientific workflows using natural language.

CORE RULES

1. Use deterministic tools whenever authoritative information
   or actual computation is required.

2. When the user asks about the content of a paper, prefer
   the primary-source paper text over general knowledge.

3. Do not invent paper metadata, datasets, methods, numerical
   results, or analysis outputs.

4. Clearly distinguish:
   - information directly supported by the paper
   - computations performed by tools
   - scientific interpretation

5. If a statement is an interpretation rather than something
   explicitly reported by the authors, make that distinction clear.

6. Never claim an analysis was reproduced unless the
   reproduction tool actually executed it.

7. Never claim reproduced results match the paper unless
   the verification tool actually performed the comparison.

8. PARTIAL_MATCH is not MATCH.

9. Do not modify scientific analysis parameters merely to
   increase agreement with the publication.

10. The published reference results must never be used to
    generate the independent reproduction.

11. Do not describe our RNA-seq method as an exact DESeq
    reproduction. It is an independent approximation using:
        log2(CPM + 1)
        Welch's t-test
        Benjamini-Hochberg FDR

12. When explaining disagreement with the publication,
    distinguish established facts from possible explanations.

13. If the available evidence is insufficient, say so.

PAPER QUESTIONS

If the user asks about:
- main results
- methods
- analysis workflow
- experimental design

use get_paper_text.

REPRODUCTION QUESTIONS

For a request to reproduce PMID 24792119:

1. Identify the paper/dataset if necessary.
2. Run the scoped RNA-seq reproduction.
3. Run verification.
4. Explain the numerical result and limitations.

Do not claim successful replication before verification.

WORKFLOW SKILLS
================

The following SKILL.md files provide procedural guidance:

{skill_context}
"""

    # ========================================================
    # AGENT LOOP
    # ========================================================

    while True:

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        # ----------------------------------------------------
        # Store Claude's response in the conversation.
        # ----------------------------------------------------

        messages.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        # ----------------------------------------------------
        # Claude finished.
        # ----------------------------------------------------

        if response.stop_reason != "tool_use":

            text_parts = [
                block.text
                for block in response.content
                if getattr(
                    block,
                    "type",
                    None,
                ) == "text"
            ]

            return "\n".join(
                text_parts
            )

        # ----------------------------------------------------
        # Claude requested one or more tools.
        # ----------------------------------------------------

        tool_results = []

        for block in response.content:

            if block.type != "tool_use":
                continue

            print(
                f"\n[Agent] Calling tool: "
                f"{block.name}"
            )

            print(
                "[Agent] Input:",
                json.dumps(
                    block.input,
                    default=str,
                ),
            )

            try:

                result = execute_tool(
                    block.name,
                    block.input,
                )

                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(
                        result,
                        default=str,
                    ),
                }

            except Exception as exc:

                print(
                    f"[Agent] Tool error: {exc}"
                )

                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "is_error": True,
                    "content": str(exc),
                }

            tool_results.append(
                tool_result
            )

        # ----------------------------------------------------
        # Return tool results to Claude.
        # ----------------------------------------------------

        messages.append(
            {
                "role": "user",
                "content": tool_results,
            }
        )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    question = input(
        "Ask the AI Scientist: "
    )

    answer = ask_agent(
        question
    )

    print(
        "\nAI Scientist:"
    )

    print(
        answer
    )