# Paper Discovery Skill

## Purpose

Identify and retrieve the scientific paper specified by the user.

The goal is to return a reliable paper record that can be used by
downstream scientific workflows.

## Inputs

- User-provided identifier such as:
  - PMID
  - DOI
  - PubMed URL
  - paper title

## Workflow

1. Resolve the paper identifier.
2. Retrieve authoritative metadata.
3. Identify:
   - title
   - authors
   - journal
   - publication year
   - DOI
   - PMID
   - abstract
   - full-text availability
4. Identify relevant supplementary resources.
5. Identify public datasets associated with the paper.
6. Identify public code repositories when available.
7. Save the paper metadata in a structured form.

## Source hierarchy

Prefer sources in this order:

1. PubMed / NCBI
2. Publisher full text
3. GEO / other official data repositories
4. Author-maintained GitHub repositories
5. Other secondary sources only when necessary

## Output

Return a structured paper record containing:

- title
- PMID
- DOI
- publication information
- abstract
- full-text URL
- datasets
- code repositories
- source URLs

## Evidence requirements

Every factual statement about the paper should be traceable
to a retrieved source.

Do not infer experimental methods, datasets, or results
when they have not been explicitly identified in the source.

## Failure handling

If the paper cannot be retrieved:

1. Report what identifier was attempted.
2. Report which source failed.
3. Try an alternative authoritative source.
4. Do not invent missing metadata.