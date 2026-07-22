"""Citation service: parse [N] references from LLM output and map to chunk metadata."""

import re
from typing import Any

CITATION_PATTERN = re.compile(r"\[(\d+(?:,\s*\d+)*)\]")
PREVIEW_MAX_CHARS = 200


def build_citation_map(chunks: list[dict]) -> dict[int, dict[str, Any]]:
    """Build a citation map from retrieved ChromaDB chunks.

    Each entry maps the 1-based citation index to:
        - ``index``: the citation number
        - ``document_name``: source document filename
        - ``page``: page number or sheet name
        - ``text_preview``: first N characters of the chunk text

    Parameters
    ----------
    chunks:
        Retrieved chunks from ChromaDB, each containing ``id``, ``document``,
        ``metadata``, and ``distance``.

    Returns
    -------
    dict[int, dict]
        Citation map keyed by 1-based index.
    """
    citation_map: dict[int, dict[str, Any]] = {}
    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        text = chunk.get("document", "")
        citation_map[i] = {
            "index": i,
            "document_name": metadata.get("document_name", "Documento"),
            "page": metadata.get("page_num", "?"),
            "text_preview": text[:PREVIEW_MAX_CHARS],
        }
    return citation_map


def parse_citations(
    response_text: str,
    citation_map: dict[int, dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Parse [N] citation references from LLM response text.

    Finds all ``[N]`` references and maps them to the citation map.
    Out-of-range indices are silently ignored.

    Parameters
    ----------
    response_text:
        The raw text produced by the LLM, which may contain ``[1]``, ``[2]``,
        etc.
    citation_map:
        Mapping from citation index to metadata, as built by
        :func:`build_citation_map`.

    Returns
    -------
    tuple[str, list[dict]]
        ``(clean_text, citations)`` where *clean_text* is the original text
        (citations left in place) and *citations* is a list of matched
        citation metadata dicts.
    """
    seen: set[int] = set()
    citations: list[dict[str, Any]] = []

    for match in CITATION_PATTERN.finditer(response_text):
        raw = match.group(1)
        # Handle both [1] and [1,2] formats
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                idx = int(part)
            except ValueError:
                continue
            if idx in citation_map and idx not in seen:
                seen.add(idx)
                citations.append(citation_map[idx])

    return response_text, citations
