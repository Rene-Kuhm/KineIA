#!/usr/bin/env python3
"""
KineIA Knowledge Base Scraper

Scrapes publicly available clinical guidelines and protocols from Argentine
medical societies for the kinesiology knowledge base.

Sources:
  SATI   — Sociedad Argentina de Terapia Intensiva (revista.sati.org.ar)
  SAMFYR — Sociedad Argentina de Medicina Física y Rehabilitación (samfyr.org.ar)
  SAPCV  — Sociedad Argentina de Patología de la Columna Vertebral (sapcv.com.ar)
  AAOT   — Asociación Argentina de Ortopedia y Traumatología (raaot.org.ar)
  INAREPs — Instituto Nacional de Rehabilitación (argentina.gob.ar/inareps)

Usage:
  python scripts/scrape_sources.py               # full scrape
  python scripts/scrape_sources.py --dry-run      # show URLs only
  python scripts/scrape_sources.py --delay 3.0    # custom delay
"""

from __future__ import annotations

import argparse
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape-sources")


# ── Configuration ────────────────────────────────────────────────────────

USER_AGENT = (
    "KineIA-KnowledgeBase/1.0 (research + educational tool; "
    "contact: kineia@example.com)"
)

DEFAULT_OUTPUT_DIR = "/tmp/KineIA/knowledge_base/guias-clinicas/scraped"
DEFAULT_DELAY = 2.5  # seconds between requests

# ── Data Classes ─────────────────────────────────────────────────────────


@dataclass
class SourceConfig:
    """Configuration for a single knowledge source to scrape."""

    name: str
    short_name: str
    base_url: str
    search_urls: list[str]
    area: str
    source_type: str = "protocol"
    evidence_level: str = "protocol"
    description: str = ""


# ── Source Definitions ───────────────────────────────────────────────────


def get_sources() -> list[SourceConfig]:
    """Return the configured list of Argentine medical society sources."""
    return [
        SourceConfig(
            name="Sociedad Argentina de Terapia Intensiva",
            short_name="SATI",
            base_url="https://revista.sati.org.ar",
            search_urls=[
                "https://revista.sati.org.ar/index.php/MI/search?query=kinesiolog%C3%ADa",
                "https://revista.sati.org.ar/index.php/MI/search?query=ventilaci%C3%B3n+mec%C3%A1nica",
                "https://revista.sati.org.ar/index.php/MI/search?query=disfagia",
                "https://revista.sati.org.ar/index.php/MI/search?query=rehabilitaci%C3%B3n+UCI",
            ],
            area="respiratorio",
            source_type="protocol",
            evidence_level="protocol",
            description="Kinesiology in ICU, mechanical ventilation, dysphagia",
        ),
        SourceConfig(
            name="Sociedad Argentina de Medicina Física y Rehabilitación",
            short_name="SAMFYR",
            base_url="https://samfyr.org.ar",
            search_urls=[
                "https://samfyr.org.ar/guias-y-consensos/",
                "https://samfyr.org.ar/publicaciones/",
            ],
            area="rehabilitacion",
            source_type="consenso",
            evidence_level="consenso",
            description="Rehabilitation guidelines and consensus documents",
        ),
        SourceConfig(
            name="Sociedad Argentina de Patología de la Columna Vertebral",
            short_name="SAPCV",
            base_url="https://sapcv.com.ar",
            search_urls=[
                "https://sapcv.com.ar/guias/",
                "https://sapcv.com.ar/publicaciones/",
            ],
            area="columna",
            source_type="protocol",
            evidence_level="protocol",
            description="Spinal pathology guidelines",
        ),
        SourceConfig(
            name="Asociación Argentina de Ortopedia y Traumatología",
            short_name="AAOT",
            base_url="https://raaot.org.ar",
            search_urls=[
                "https://raaot.org.ar/revista/",
                "https://raaot.org.ar/biblioteca/",
            ],
            area="traumatologia",
            source_type="protocol",
            evidence_level="protocol",
            description="Orthopedic rehabilitation protocols",
        ),
        SourceConfig(
            name="Instituto Nacional de Rehabilitación Psicofísica del Sur",
            short_name="INAREPs",
            base_url="https://www.argentina.gob.ar/salud/inareps",
            search_urls=[
                "https://www.argentina.gob.ar/salud/inareps/guias",
                "https://www.argentina.gob.ar/salud/inareps/publicaciones",
            ],
            area="rehabilitacion",
            source_type="guia",
            evidence_level="guia-oficial",
            description="National rehabilitation guidelines (public domain)",
        ),
    ]


# ── Pure Functions ───────────────────────────────────────────────────────


def sanitize_filename(title: str, max_length: int = 120) -> str:
    """Convert a document title to a safe filesystem filename.

    Strips accents, removes special characters, replaces spaces with hyphens,
    truncates to max_length, and appends .md extension.
    """
    if not title or not title.strip():
        return "untitled.md"

    # Normalize unicode: decompose accented chars, drop combining marks
    normalized = unicodedata.normalize("NFKD", title.strip())

    # Keep only ASCII alphanumeric, spaces, and hyphens
    ascii_chars = []
    for ch in normalized:
        if ch.isascii() and (ch.isalnum() or ch in (" ", "-", "_")):
            ascii_chars.append(ch)
        elif ch == " ":
            ascii_chars.append("-")

    cleaned = "".join(ascii_chars)

    # Replace spaces with hyphens, collapse multiple hyphens
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    cleaned = cleaned.strip("-")

    if not cleaned:
        return "untitled.md"

    # Truncate
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip("-")

    return f"{cleaned}.md"


def generate_frontmatter(
    title: str,
    source: str,
    source_type: str,
    area: str,
    evidence_level: str,
    year: int,
    url: str,
) -> str:
    """Generate YAML-like frontmatter for a scraped knowledge base document.

    Returns a string starting and ending with '---' containing the metadata.
    """
    escaped_title = title.replace('"', '\\"')
    escaped_source = source.replace('"', '\\"')
    escaped_url = url.replace('"', '\\"')

    lines = [
        "---",
        f'title: "{escaped_title}"',
        f'source: "{escaped_source}"',
        f'source_type: "{source_type}"',
        f'area: "{area}"',
        f'evidence_level: "{evidence_level}"',
        f"year: {year}",
        f'url: "{escaped_url}"',
        "---",
    ]
    return "\n".join(lines) + "\n"


# ── CLI ──────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the scraper."""
    parser = argparse.ArgumentParser(
        description="KineIA Knowledge Base Scraper — scrapes Argentine medical guidelines",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print URLs that would be scraped without actually fetching them",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save scraped Markdown files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay in seconds between requests (default: {DEFAULT_DELAY})",
    )
    return parser.parse_args(argv)


# ── Robots.txt ───────────────────────────────────────────────────────────


def check_robots_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    """Check if scraping the given URL is allowed by the site's robots.txt.

    Returns True if allowed (or if robots.txt is unreachable — we err on
    the side of permissiveness only when the file itself is unavailable).
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.allow_all = True  # default: allow if robots.txt is unreachable
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        log.warning("Could not fetch robots.txt for %s — assuming allowed", parsed.netloc)
        return True

    return rp.can_fetch(user_agent, url)


# ── HTTP Client ──────────────────────────────────────────────────────────


def create_client(timeout: int = 30) -> httpx.Client:
    """Create an httpx client with the KineIA research user agent."""
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
        follow_redirects=True,
    )


# ── Content Extraction ───────────────────────────────────────────────────


def extract_text_from_html(html: str, url: str) -> str:
    """Extract readable text content from an HTML page.

    Attempts to find article/main content areas first, falls back to
    extracting all paragraph text from the body.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer, header elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try to find main content container
    content_selectors = [
        "article",
        "main",
        '[role="main"]',
        ".content",
        ".post-content",
        ".entry-content",
        ".article-content",
        "#content",
        "#main-content",
        ".main-content",
    ]

    content = None
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            break

    if content is None:
        content = soup.find("body") or soup

    # Extract paragraphs and headers
    elements = content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"])
    if not elements:
        # Fallback: get all text
        text = content.get_text(separator="\n", strip=True)
        return text

    lines = []
    for el in elements:
        tag = el.name.lower()
        text = el.get_text(strip=True)
        if not text:
            continue

        if tag.startswith("h"):
            level = int(tag[1])
            prefix = "#" * level
            lines.append(f"\n{prefix} {text}\n")
        elif tag == "blockquote":
            lines.append(f"> {text}")
        elif tag == "li":
            lines.append(f"- {text}")
        else:
            lines.append(f"\n{text}\n")

    return "\n".join(lines)


def extract_title_from_html(html: str) -> str:
    """Extract the document title from an HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    # Try <title> tag first
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        # Remove site name suffix (common pattern: "Title | Site Name")
        title = re.split(r"\s*[|\-–—]\s*", title)[0].strip()
        return title

    # Try h1
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)

    return "Untitled Document"


def extract_year_from_html(html: str, url: str) -> int:
    """Attempt to extract the publication year from HTML or URL."""
    soup = BeautifulSoup(html, "html.parser")

    # Try meta tags
    for meta in soup.find_all("meta"):
        name = meta.get("name", "").lower()
        prop = meta.get("property", "").lower()
        content = meta.get("content", "")
        if name in ("date", "pubdate", "dc.date") or prop in (
            "article:published_time",
            "og:article:published_time",
        ):
            match = re.search(r"(\d{4})", str(content))
            if match:
                return int(match.group(1))

    # Try to find year in visible text near "publicado" or "fecha"
    text = soup.get_text()[:2000]
    for pattern in [
        r"(?:publicad[oa]|fecha|año)[:\s]*(\d{4})",
        r"©\s*(\d{4})",
        r"(\d{4})\s*[-–]\s*\d{4}",  # year range
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Try to find a 4-digit year in the URL
    match = re.search(r"/(\d{4})/", url)
    if match:
        return int(match.group(1))

    return datetime.now().year


# ── Scraper ──────────────────────────────────────────────────────────────


def scrape_source(
    source: SourceConfig,
    client: httpx.Client,
    output_dir: Path,
    delay: float,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Scrape a single source, saving documents to output_dir/short_name/.

    Returns (documents_scraped, errors).
    """
    source_dir = output_dir / source.short_name.lower()
    if not dry_run:
        source_dir.mkdir(parents=True, exist_ok=True)

    docs = 0
    errors = 0

    for search_url in source.search_urls:
        if dry_run:
            log.info("[DRY-RUN] Would scrape: %s", search_url)
            continue

        try:
            # Respect robots.txt
            if not check_robots_allowed(search_url):
                log.warning("Blocked by robots.txt: %s", search_url)
                errors += 1
                continue

            log.info("Fetching: %s", search_url)
            response = client.get(search_url)
            response.raise_for_status()

            # Check for auth wall / login page
            if _is_auth_wall(response):
                log.warning("Auth wall detected — skipping: %s", search_url)
                errors += 1
                continue

            html = response.text

            # Extract article links from the search/page
            article_urls = _find_article_links(html, source, search_url)
            log.info("  Found %d potential articles on %s", len(article_urls), search_url)

            for article_url in article_urls[:10]:  # Limit per page
                time.sleep(delay)

                try:
                    if not check_robots_allowed(article_url):
                        log.debug("  Blocked by robots.txt: %s", article_url)
                        continue

                    art_response = client.get(article_url)
                    art_response.raise_for_status()

                    if _is_auth_wall(art_response):
                        log.debug("  Auth wall: %s", article_url)
                        continue

                    art_html = art_response.text

                    title = extract_title_from_html(art_html)
                    content = extract_text_from_html(art_html, article_url)
                    year = extract_year_from_html(art_html, article_url)

                    if not content or len(content.strip()) < 50:
                        log.debug("  Skipping (too little content): %s", article_url)
                        continue

                    # Build frontmatter + content
                    frontmatter = generate_frontmatter(
                        title=title,
                        source=source.short_name,
                        source_type=source.source_type,
                        area=source.area,
                        evidence_level=source.evidence_level,
                        year=year,
                        url=article_url,
                    )

                    filename = sanitize_filename(title)
                    filepath = source_dir / filename

                    # Avoid overwriting — append number if collision
                    counter = 1
                    while filepath.exists():
                        stem = filename.rsplit(".", 1)[0]
                        filepath = source_dir / f"{stem}-{counter}.md"
                        counter += 1

                    filepath.write_text(frontmatter + "\n" + content, encoding="utf-8")
                    docs += 1
                    log.info("  ✓ Saved: %s", filepath.name)

                except httpx.HTTPError as e:
                    log.warning("  HTTP error for %s: %s", article_url, e)
                    errors += 1
                except Exception as e:
                    log.warning("  Unexpected error for %s: %s", article_url, e)
                    errors += 1

        except httpx.HTTPError as e:
            log.warning("HTTP error fetching %s: %s", search_url, e)
            errors += 1
        except Exception as e:
            log.warning("Unexpected error for %s: %s", search_url, e)
            errors += 1

    return docs, errors


def _is_auth_wall(response: httpx.Response) -> bool:
    """Heuristic check: does the response look like a login/auth page?"""
    text = response.text.lower()[:2000]
    auth_indicators = [
        "iniciar sesión",
        "iniciar sesion",
        "log in",
        "login",
        "password",
        "contraseña",
        "registrarse",
        "suscribirse",
        "acceso restringido",
        "acceso exclusivo",
        "members only",
        "paywall",
        "subscribe",
    ]
    # Only flag if the page is dominated by auth content (not just mentions)
    count = sum(1 for ind in auth_indicators if ind in text)
    # Also check status code
    if response.status_code in (401, 403):
        return True
    return count >= 3


def _find_article_links(
    html: str,
    source: SourceConfig,
    base_url: str,
) -> list[str]:
    """Find article/document links on a listing page.

    Filters for links that look like articles (contain dates, specific
    paths, etc.) and belong to the same domain.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)

        # Only same-domain links
        if urlparse(full_url).netloc != base_domain:
            continue

        # Skip non-content links
        skip_patterns = [
            "/author/",
            "/category/",
            "/tag/",
            "/about",
            "/contact",
            "/login",
            "/wp-admin",
            "/feed",
            "/page/",
            "#",
            "javascript:",
            "mailto:",
        ]
        if any(p in href.lower() for p in skip_patterns):
            continue

        # Look for content-indicating patterns in URL
        content_indicators = [
            "/index.php/",
            "/article/",
            "/articulo/",
            "/publicacion/",
            "/guia/",
            "/protocolo/",
            "/noticia/",
            "/documento/",
            "/revista/",
            "/view/",
            "/ver/",
        ]
        # Also accept links where the anchor text is substantial
        anchor_text = a_tag.get_text(strip=True)

        is_content_url = any(p in href.lower() for p in content_indicators)
        has_substantial_text = len(anchor_text) > 20

        if is_content_url or has_substantial_text:
            links.add(full_url)

    return list(links)


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> None:
    """Entry point — parse args, scrape all sources, print summary."""
    args = parse_args()

    log.info("=" * 60)
    log.info("KineIA Knowledge Base Scraper")
    log.info("=" * 60)
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "LIVE")
    log.info("Output: %s", args.output_dir)
    log.info("Delay: %.1fs between requests", args.delay)
    log.info("Sources: %d configured", len(get_sources()))

    if args.dry_run:
        log.info("\n--- URL Preview ---")
        for source in get_sources():
            log.info("\n[%s] %s", source.short_name, source.name)
            for url in source.search_urls:
                log.info("  → %s", url)
        log.info("\n--- End Preview ---")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = create_client()
    total_docs = 0
    total_errors = 0
    failed_sources: list[str] = []

    try:
        for source in get_sources():
            log.info("\n── %s ──", source.short_name)
            docs, errors = scrape_source(
                source, client, output_dir, args.delay, dry_run=False
            )
            total_docs += docs
            total_errors += errors
            if docs == 0 and errors > 0:
                failed_sources.append(source.short_name)

    finally:
        client.close()

    # Summary
    log.info("\n" + "=" * 60)
    log.info("SCRAPE COMPLETE")
    log.info("=" * 60)
    log.info("  Documents scraped: %d", total_docs)
    log.info("  Errors: %d", total_errors)
    if failed_sources:
        log.info("  Failed sources: %s", ", ".join(failed_sources))
    log.info("  Output directory: %s", output_dir)


if __name__ == "__main__":
    main()
