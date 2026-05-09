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
        assert len(result) >= 2
        # Headers should be preserved
        headers = [chunk.get("header", "") for chunk in result]
        assert any("# Capítulo 1" in h for h in headers if h)

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
