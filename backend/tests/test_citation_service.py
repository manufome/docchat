"""Tests for the citation service.

RED→GREEN→REFACTOR: Citation parsing from LLM response text.
"""

from app.services.citation_service import (
    build_citation_map,
    parse_citations,
)


class TestParseCitations:
    """Citation parsing from LLM response text."""

    def test_parse_single_citation(self):
        """GIVEN text with [1] WHEN parsed THEN citation extracted, text unchanged."""
        text = "El gato es negro[1]."
        clean, citations = parse_citations(text, {1: {"index": 1, "document_name": "doc.pdf", "page": 3, "text_preview": "gato"}})
        assert len(citations) == 1
        assert citations[0]["index"] == 1
        assert "El gato es negro[1]." == clean

    def test_parse_multiple_citations(self):
        """GIVEN text with [1] and [2] WHEN parsed THEN both extracted."""
        text = "Texto A[1] y texto B[2]."
        citation_map = {
            1: {"index": 1, "document_name": "a.pdf", "page": 1, "text_preview": "Texto A"},
            2: {"index": 2, "document_name": "b.pdf", "page": 2, "text_preview": "Texto B"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 2
        indices = [c["index"] for c in citations]
        assert 1 in indices
        assert 2 in indices

    def test_no_citations(self):
        """GIVEN text without [N] references WHEN parsed THEN empty list."""
        clean, citations = parse_citations("Texto sin referencias.", {})
        assert citations == []
        assert clean == "Texto sin referencias."

    def test_citation_metadata_preserved(self):
        """GIVEN citation map WHEN parsed THEN metadata included."""
        text = "Resultado[1]."
        citation_map = {
            1: {"index": 1, "document_name": "reporte.pdf", "page": 5, "text_preview": "Resultado importante"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert citations[0]["document_name"] == "reporte.pdf"
        assert citations[0]["page"] == 5
        assert citations[0]["text_preview"] == "Resultado importante"

    def test_out_of_range_index(self):
        """GIVEN [3] with only 2 citations in map WHEN parsed THEN ignored."""
        text = "Algo[3]."
        citation_map = {
            1: {"index": 1, "document_name": "a.pdf", "page": 1, "text_preview": "Algo"},
            2: {"index": 2, "document_name": "b.pdf", "page": 2, "text_preview": "Algo"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 0

    def test_consecutive_citations(self):
        """GIVEN [1][2] consecutive WHEN parsed THEN both captured."""
        text = "Afirmación[1][2]."
        citation_map = {
            1: {"index": 1, "document_name": "a.pdf", "page": 1, "text_preview": "A"},
            2: {"index": 2, "document_name": "b.pdf", "page": 2, "text_preview": "B"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 2

    def test_citation_ends_with_period(self):
        """GIVEN text like 'gato[1].' WHEN parsed THEN citation extracted."""
        text = "El resultado es claro[1]."
        citation_map = {
            1: {"index": 1, "document_name": "doc.pdf", "page": 1, "text_preview": "claro"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 1
        assert citations[0]["index"] == 1

    def test_comma_separated_citations(self):
        """GIVEN [1,2] format WHEN parsed THEN both citations captured."""
        text = "Múltiples fuentes[1,2]."
        citation_map = {
            1: {"index": 1, "document_name": "a.pdf", "page": 1, "text_preview": "A"},
            2: {"index": 2, "document_name": "b.pdf", "page": 2, "text_preview": "B"},
        }
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 2
        assert {c["index"] for c in citations} == {1, 2}

    def test_double_digit_citation(self):
        """GIVEN [10] with double digit WHEN parsed THEN extracted."""
        text = "Referencia[10]."
        citation_map = {10: {"index": 10, "document_name": "x.pdf", "page": 10, "text_preview": "X"}}
        clean, citations = parse_citations(text, citation_map)
        assert len(citations) == 1
        assert citations[0]["index"] == 10


class TestBuildCitationMap:
    """Build citation map from ChromaDB chunks."""

    def test_builds_citation_map(self):
        """GIVEN chunks WHEN build_citation_map THEN correct indices."""
        chunks = [
            {"metadata": {"document_name": "doc.pdf", "page_num": 2}, "document": "La capital de Francia es París."},
            {"metadata": {"document_name": "doc.pdf", "page_num": 3}, "document": "París tiene la Torre Eiffel."},
        ]
        citation_map = build_citation_map(chunks)
        assert len(citation_map) == 2
        assert citation_map[1]["document_name"] == "doc.pdf"
        assert citation_map[1]["page"] == 2
        assert citation_map[1]["text_preview"] == "La capital de Francia es París."
        assert citation_map[2]["document_name"] == "doc.pdf"

    def test_text_preview_truncated(self):
        """GIVEN long text WHEN build_citation_map THEN preview truncated to 200 chars."""
        chunks = [
            {"metadata": {"document_name": "doc.pdf", "page_num": 1}, "document": "A" * 300},
        ]
        citation_map = build_citation_map(chunks)
        assert len(citation_map[1]["text_preview"]) == 200

    def test_empty_chunks(self):
        """GIVEN empty chunks WHEN build_citation_map THEN empty dict."""
        assert build_citation_map([]) == {}
