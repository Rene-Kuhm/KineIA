"""Tests for scrape_sources.py — KineIA knowledge base scraper."""

import sys
from datetime import datetime
from pathlib import Path

# Add scripts dir to path so we can import scrape_sources
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import httpx
from scrape_sources import (
    SourceConfig,
    _is_auth_wall,
    extract_text_from_html,
    extract_title_from_html,
    extract_year_from_html,
    generate_frontmatter,
    get_sources,
    parse_args,
    sanitize_filename,
)

# ── sanitize_filename ────────────────────────────────────────────────────


class TestSanitizeFilename:
    """Pure function — sanitizes document titles to valid filenames."""

    def test_basic_title_with_spaces(self):
        """Spaces become hyphens, special chars removed, extension added."""
        result = sanitize_filename("Guía de Ventilación Mecánica en UCI")
        assert " " not in result
        assert result.endswith(".md")
        assert "Guia" in result  # accents stripped, not preserved

    def test_title_with_special_characters(self):
        """Slashes, colons, and question marks are stripped."""
        result = sanitize_filename("Rehabilitación: ¿Cómo y cuándo empezar?")
        assert "/" not in result
        assert ":" not in result
        assert "¿" not in result
        assert "?" not in result
        assert result.endswith(".md")

    def test_very_long_title_truncated(self):
        """Titles longer than 120 chars are truncated."""
        long_title = "A" * 200
        result = sanitize_filename(long_title)
        assert len(result) <= 128  # 120 + ".md"
        assert result.endswith(".md")

    def test_empty_title_returns_untitled(self):
        """Empty or whitespace-only title returns 'untitled.md'."""
        result = sanitize_filename("   ")
        assert result == "untitled.md"

    def test_accented_characters_normalized(self):
        """Accented Spanish characters are stripped to ASCII-safe equivalents."""
        result = sanitize_filename("Kinesiología en UCI")
        assert result.endswith(".md")
        # Should not contain raw accented chars in filename
        assert "ó" not in result and "í" not in result

    def test_leading_trailing_spaces_trimmed(self):
        """Leading and trailing spaces don't produce leading/trailing hyphens."""
        result = sanitize_filename("  Guía Rápida  ")
        assert not result.startswith("-")
        assert not result.startswith(" ")
        assert "Guia-Rapida" in result

    def test_multiple_consecutive_spaces_collapsed(self):
        """Multiple spaces become a single hyphen, not multiple hyphens."""
        result = sanitize_filename("Guía    con    muchos    espacios")
        assert "----" not in result
        assert result.endswith(".md")

    def test_numbers_preserved(self):
        """Numeric characters are preserved in the filename."""
        result = sanitize_filename("Protocolo COVID-19 Fase 2")
        assert "19" in result
        assert "2" in result

    def test_only_special_chars_returns_untitled(self):
        """Title consisting only of special characters returns untitled.md."""
        result = sanitize_filename("¿¡?!@#$%^&*()")
        assert result == "untitled.md"


# ── generate_frontmatter ─────────────────────────────────────────────────


class TestGenerateFrontmatter:
    """Pure function — generates YAML frontmatter for Markdown documents."""

    def test_basic_frontmatter_structure(self):
        """Frontmatter has opening/closing ---, and all required fields."""
        fm = generate_frontmatter(
            title="Protocolo de Destete",
            source="SATI",
            source_type="protocol",
            area="respiratorio",
            evidence_level="protocol",
            year=2024,
            url="https://example.com/doc",
        )
        assert fm.startswith("---\n")
        assert fm.endswith("---\n")
        assert 'title: "Protocolo de Destete"' in fm
        assert 'source: "SATI"' in fm
        assert 'source_type: "protocol"' in fm
        assert 'area: "respiratorio"' in fm
        assert 'evidence_level: "protocol"' in fm
        assert "year: 2024" in fm
        assert 'url: "https://example.com/doc"' in fm

    def test_quotes_in_title_are_escaped(self):
        """Double quotes inside the title are escaped."""
        fm = generate_frontmatter(
            title='Guía "Oro" para Kinesiólogos',
            source="SAMFYR",
            source_type="consenso",
            area="rehabilitacion",
            evidence_level="consenso",
            year=2023,
            url="https://samfyr.org.ar/guia",
        )
        assert 'title: "Guía \\"Oro\\" para Kinesiólogos"' in fm

    def test_all_fields_present_in_correct_order(self):
        """Frontmatter fields appear in the expected order."""
        fm = generate_frontmatter(
            title="T",
            source="S",
            source_type="ST",
            area="A",
            evidence_level="EL",
            year=2022,
            url="https://u.rl",
        )
        lines = fm.strip().split("\n")
        field_order = ["title", "source", "source_type", "area", "evidence_level", "year", "url"]
        found_fields = [line.split(":")[0].strip() for line in lines[1:-1]]
        assert found_fields == field_order

    def test_empty_url_handled(self):
        """Empty URL string is still included in frontmatter."""
        fm = generate_frontmatter(
            title="Test",
            source="SRC",
            source_type="t",
            area="a",
            evidence_level="e",
            year=2025,
            url="",
        )
        assert 'url: ""' in fm

    def test_inareps_source_name_included(self):
        """INAREPs full source name appears correctly in frontmatter."""
        fm = generate_frontmatter(
            title="Guía de Rehabilitación",
            source="INAREPs",
            source_type="guia",
            area="rehabilitacion",
            evidence_level="guia-oficial",
            year=2025,
            url="https://argentina.gob.ar/doc",
        )
        assert 'source: "INAREPs"' in fm
        assert 'source_type: "guia"' in fm
        assert 'evidence_level: "guia-oficial"' in fm


# ── Content Extraction ───────────────────────────────────────────────────


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Protocolo de Ventilación Mecánica — SATI</title></head>
<body>
<article>
  <h1>Protocolo de Ventilación Mecánica en UCI</h1>
  <p>Este documento describe los procedimientos para la ventilación mecánica
  en unidades de cuidados intensivos.</p>
  <p>Incluye criterios de destete y manejo de la vía aérea.</p>
  <h2>Criterios de Inclusión</h2>
  <ul>
    <li>Pacientes adultos mayores de 18 años</li>
    <li>Con insuficiencia respiratoria aguda</li>
  </ul>
</article>
<footer>© 2024 SATI</footer>
</body>
</html>"""

SAMPLE_HTML_NO_ARTICLE = """<!DOCTYPE html>
<html>
<head><title>Página sin estructura</title></head>
<body>
  <p>Contenido suelto sin article ni main.</p>
  <p>Otro párrafo de información.</p>
</body>
</html>"""

SAMPLE_HTML_AUTH_WALL = """<!DOCTYPE html>
<html>
<head><title>Iniciar Sesión</title></head>
<body>
  <h1>Acceso Restringido</h1>
  <p>Debe iniciar sesión para ver este contenido.</p>
  <form>
    <input type="text" name="username" placeholder="Usuario">
    <input type="password" name="password" placeholder="Contraseña">
    <button>Iniciar Sesión</button>
  </form>
</body>
</html>"""


class TestExtractTitle:
    """Content extraction — title detection from HTML."""

    def test_extracts_from_title_tag(self):
        """Title is extracted from the <title> tag and site suffix stripped."""
        result = extract_title_from_html(SAMPLE_HTML)
        assert "Protocolo de Ventilación Mecánica" in result

    def test_falls_back_to_h1(self):
        """When <title> is absent, falls back to <h1>."""
        html = "<html><body><h1>Documento Principal</h1></body></html>"
        result = extract_title_from_html(html)
        assert result == "Documento Principal"

    def test_untitled_when_no_title_or_h1(self):
        """Returns 'Untitled Document' when no title or h1 found."""
        html = "<html><body><p>Just a paragraph</p></body></html>"
        result = extract_title_from_html(html)
        assert result == "Untitled Document"


class TestExtractText:
    """Content extraction — text extraction from HTML."""

    def test_extracts_paragraphs_from_article(self):
        """Paragraphs and headers are extracted from <article> element."""
        result = extract_text_from_html(SAMPLE_HTML, "https://test.org/doc")
        assert "procedimientos para la ventilación" in result.lower()
        assert "## Criterios de Inclusión" in result
        assert "- Pacientes adultos" in result

    def test_falls_back_to_body_when_no_article(self):
        """When no article/main, extracts from <body>."""
        result = extract_text_from_html(SAMPLE_HTML_NO_ARTICLE, "https://test.org/doc")
        assert "Contenido suelto" in result
        assert "Otro párrafo" in result

    def test_script_and_style_tags_removed(self):
        """Script and style content does not appear in output."""
        html = """<html><body><article>
        <p>Visible content</p>
        <script>console.log('hidden');</script>
        <style>.hidden { display: none; }</style>
        </article></body></html>"""
        result = extract_text_from_html(html, "https://test.org/doc")
        assert "console.log" not in result
        assert "hidden" not in result.lower()


class TestExtractYear:
    """Content extraction — year detection from HTML and URL."""

    def test_extracts_from_meta_published_time(self):
        """Year is extracted from og:article:published_time meta tag."""
        html = (
            '<html><head>'
            '<meta property="article:published_time" content="2023-06-15">'
            '</head><body></body></html>'
        )
        result = extract_year_from_html(html, "https://test.org/doc")
        assert result == 2023

    def test_extracts_from_url_path(self):
        """Year is extracted from /2024/ path in URL as fallback."""
        html = "<html><body></body></html>"
        result = extract_year_from_html(html, "https://revista.sati.org.ar/2022/articulo")
        assert result == 2022

    def test_returns_current_year_as_last_resort(self):
        """Returns current year when no other source available."""
        html = "<html><body></body></html>"
        result = extract_year_from_html(html, "https://test.org/no-date")
        assert result == datetime.now().year


class TestIsAuthWall:
    """Heuristic — auth wall detection."""

    def test_detects_login_page(self):
        """Page with login form and password field is detected as auth wall."""
        response = httpx.Response(200, content=SAMPLE_HTML_AUTH_WALL.encode())
        assert _is_auth_wall(response) is True

    def test_normal_article_not_auth_wall(self):
        """Normal article content is not flagged as auth wall."""
        response = httpx.Response(200, content=SAMPLE_HTML.encode())
        assert _is_auth_wall(response) is False

    def test_401_status_is_auth_wall(self):
        """HTTP 401 status code is always treated as auth wall."""
        response = httpx.Response(401)
        assert _is_auth_wall(response) is True

    def test_403_status_is_auth_wall(self):
        """HTTP 403 status code is always treated as auth wall."""
        response = httpx.Response(403)
        assert _is_auth_wall(response) is True


# ── SourceConfig ─────────────────────────────────────────────────────────


class TestSourceConfig:
    """Structural test — SourceConfig dataclass validation."""

    def test_valid_source_config_creation(self):
        """SourceConfig accepts all required fields."""
        config = SourceConfig(
            name="Test Society",
            short_name="TEST",
            base_url="https://test.org.ar",
            search_urls=["https://test.org.ar/articulos"],
            area="test-area",
        )
        assert config.name == "Test Society"
        assert config.short_name == "TEST"
        assert config.base_url == "https://test.org.ar"
        assert len(config.search_urls) == 1
        assert config.area == "test-area"

    def test_all_required_fields_are_present(self):
        """Each SourceConfig must have name, short_name, base_url, search_urls, area."""
        config = SourceConfig(
            name="S",
            short_name="S",
            base_url="https://s.org",
            search_urls=["https://s.org/a"],
            area="a",
        )
        assert config.name
        assert config.short_name
        assert config.base_url
        assert config.search_urls
        assert config.area


# ── get_sources ──────────────────────────────────────────────────────────


class TestGetSources:
    """Integration-style — all 5 source configs are well-formed."""

    def test_returns_five_sources(self):
        """get_sources() returns exactly 5 configured sources."""
        sources = get_sources()
        assert len(sources) == 5

    def test_each_source_has_search_urls(self):
        """Every source has at least one search URL defined."""
        for source in get_sources():
            assert len(source.search_urls) >= 1, f"{source.short_name} has no search URLs"

    def test_each_source_has_unique_short_name(self):
        """Short names are unique across all sources."""
        names = [s.short_name for s in get_sources()]
        assert len(names) == len(set(names))

    def test_all_expected_sources_present(self):
        """SATI, SAMFYR, SAPCV, AAOT, INAREPs are all configured."""
        names = {s.short_name for s in get_sources()}
        expected = {"SATI", "SAMFYR", "SAPCV", "AAOT", "INAREPs"}
        assert names == expected

    def test_sources_have_valid_urls(self):
        """All base and search URLs use http or https scheme."""
        for source in get_sources():
            assert source.base_url.startswith("http")
            for url in source.search_urls:
                assert url.startswith("http"), f"{source.short_name}: {url}"


# ── CLI Argument Parsing ─────────────────────────────────────────────────


class TestParseArgs:
    """Argparse — CLI interface for the scraper."""

    def test_default_values(self):
        """Default run: no dry-run, default output dir, default delay."""
        args = parse_args([])
        assert args.dry_run is False
        assert args.output_dir == "/tmp/KineIA/knowledge_base/guias-clinicas/scraped"
        assert args.delay == 2.5

    def test_dry_run_flag_enabled(self):
        """--dry-run sets the flag to True."""
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_custom_output_dir(self):
        """--output-dir overrides the default."""
        args = parse_args(["--output-dir", "/tmp/custom"])
        assert args.output_dir == "/tmp/custom"

    def test_custom_delay(self):
        """--delay overrides the default request delay."""
        args = parse_args(["--delay", "5.0"])
        assert args.delay == 5.0
