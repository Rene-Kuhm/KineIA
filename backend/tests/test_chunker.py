# ruff: noqa: E501
from app.core.ingestion.chunker import chunk_text


class TestChunkText:
    def test_basic_chunking(self):
        text = "Palabra uno dos tres cuatro cinco seis siete ocho nueve diez."
        result = chunk_text(text, chunk_size=5, chunk_overlap=0)
        assert len(result) > 0
        assert all("text" in chunk for chunk in result)
        assert all("header" in chunk for chunk in result)
        assert all("word_count" in chunk for chunk in result)

    def test_chunk_preserves_content(self):
        text = (
            "La kinesiología es fundamental para la rehabilitación. "
            "Los profesionales deben conocer anatomía y fisiología. "
            "El tratamiento incluye ejercicios terapéuticos específicos."
        )
        result = chunk_text(text, chunk_size=100, chunk_overlap=0)
        # All text should be covered across chunks (minus whitespace differences)
        combined = " ".join(chunk["text"] for chunk in result)
        # Key terms should appear
        assert "kinesiología" in combined
        assert "rehabilitación" in combined
        assert "anatomía" in combined

    def test_chunk_with_headers(self):
        text = (
            "# Capítulo 1\n\n"
            "Contenido del capítulo uno. Este es un párrafo de prueba.\n\n"
            "## Sección 1.1\n\n"
            "Esta es una subsección con más contenido detallado.\n\n"
            "Otro párrafo dentro de la misma sección.\n\n"
            "# Capítulo 2\n\n"
            "Contenido del segundo capítulo."
        )
        result = chunk_text(text, chunk_size=50, chunk_overlap=0)
        assert [chunk["header"] for chunk in result] == [
            "# Capítulo 1",
            "## Sección 1.1",
            "# Capítulo 2",
        ]
        assert "Contenido del capítulo uno" in result[0]["text"]
        assert "subsección con más contenido" in result[1]["text"]
        assert "Contenido del segundo capítulo" in result[2]["text"]

    def test_header_only_document_without_final_newline(self):
        result = chunk_text("# Encabezado final", chunk_size=50, chunk_overlap=0)
        assert result == [{
            "text": "# Encabezado final",
            "header": "# Encabezado final",
            "word_count": 3,
            "section_heading": "Encabezado final",
            "section_path": ["Encabezado final"],
        }]

    def test_final_header_only_section_keeps_its_header(self):
        result = chunk_text("# Primera\n\nContenido.\n\n# Final", chunk_size=50, chunk_overlap=0)
        assert [(chunk["header"], chunk["text"]) for chunk in result] == [
            ("# Primera", "# Primera\n\nContenido."),
            ("# Final", "# Final"),
        ]

    def test_consecutive_headers_without_blank_line_keep_ownership(self):
        result = chunk_text(
            "# Principal\n## Subsección\nContenido.", chunk_size=50, chunk_overlap=0
        )
        assert [(chunk["header"], chunk["text"]) for chunk in result] == [
            ("# Principal", "# Principal"),
            ("## Subsección", "## Subsección\nContenido."),
        ]

    def test_h1_to_h6_preserve_hierarchy_and_reset_siblings(self):
        expected = [("A", ["A"]), ("D", ["A", "D"]), ("C", ["A", "C"]), ("F", ["A", "C", "F"]), ("B", ["A", "B"])]
        for newline in ("\n", "\r\n"):
            text = newline.join(("# A", "#### D", "### C", "###### F", "Detalle.", "## B", "Contenido."))
            result = chunk_text(text, chunk_size=50, chunk_overlap=0)
            assert [(chunk["section_heading"], chunk["section_path"]) for chunk in result] == expected

    def test_invalid_heading_makes_its_locator_and_descendants_unavailable(self):
        for invalid in ("   ", "x" * 201, "unsafe\x00heading", "unsafe\vheading", "unsafe\u2028heading", "unsafe\u2029heading"):
            result = chunk_text(
                f"# Root\n#### {invalid}\n##### Child\nBody.\n#### Sibling\n### Higher\nNext.",
                chunk_size=50,
                chunk_overlap=0,
            )
            assert all(chunk["section_path"] is None for chunk in result[1:3])
            assert [chunk["section_path"] for chunk in result[-2:]] == [
                ["Root", "Sibling"], ["Root", "Higher"]]

    def test_blank_heading_is_a_boundary_without_fabricating_a_locator(self):
        for newline in ("\n", "\r\n"):
            result = chunk_text(newline.join(("# Root", "Intro", "# ", "Secret")), chunk_size=50, chunk_overlap=0)
            assert [chunk["section_heading"] for chunk in result] == ["Root", None]
            assert [chunk["section_path"] for chunk in result] == [["Root"], None]
            assert "Intro" in result[0]["text"] and "Secret" in result[1]["text"]

    def test_empty_text(self):
        result = chunk_text("", chunk_size=100, chunk_overlap=10)
        assert result == []

    def test_whitespace_text(self):
        result = chunk_text("   \n\n  \n  ", chunk_size=100, chunk_overlap=10)
        assert result == []

    def test_single_word(self):
        result = chunk_text("Hola", chunk_size=100, chunk_overlap=10)
        assert len(result) == 1
        assert result[0]["text"] == "Hola"
        assert result[0]["word_count"] == 1

    def test_overlap_parameter(self):
        text = "palabra" + " extra" * 100  # Lots of words
        result_no_overlap = chunk_text(text, chunk_size=5, chunk_overlap=0)
        result_with_overlap = chunk_text(text, chunk_size=5, chunk_overlap=2)
        # With overlap, there should be more chunks covering the same content
        assert len(result_with_overlap) >= len(result_no_overlap)

    def test_chunk_boundaries(self):
        """Long paragraph should be split without losing words."""
        words = ["kinesiologia"] * 200
        text = " ".join(words)
        result = chunk_text(text, chunk_size=50, chunk_overlap=10)
        # All chunks should have reasonable word counts
        for chunk in result:
            assert chunk["word_count"] <= 50 + 10  # Allow overlap exceeding chunk_size
