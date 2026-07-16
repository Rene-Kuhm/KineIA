import hashlib
import re
from dataclasses import asdict, dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")
_OPTIONAL_FIELDS = (
    "edition", "publisher", "license", "rights", "author", "acquisition_date", "reviewer",
    "review_date", "review_due_date", "evidence_level", "area", "population", "source_type",
)


def _text(value: object) -> str | None:
    normalized = " ".join(str(value).strip().split()) if value is not None else ""
    return normalized or None


def _normalize_doi(value: object) -> str | None:
    doi = _text(value)
    if not doi:
        return None
    doi = re.sub(r"^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)", "", doi, flags=re.I)
    doi = doi.rstrip(". ").casefold()
    return doi if _DOI_PATTERN.fullmatch(doi) else None


def _normalize_isbn(value: object) -> str | None:
    isbn = re.sub(r"[^0-9Xx]", "", str(value or "")).upper()
    if len(isbn) == 10:
        total = sum((10 - i) * (10 if char == "X" else int(char)) for i, char in enumerate(isbn))
        return isbn if total % 11 == 0 else None
    if len(isbn) == 13 and isbn.isdigit():
        total = sum(int(char) * (1 if i % 2 == 0 else 3) for i, char in enumerate(isbn[:-1]))
        return isbn if (10 - total % 10) % 10 == int(isbn[-1]) else None
    return None


def _normalize_url(value: object) -> str | None:
    raw = _text(value)
    if not raw:
        return None
    try:
        parsed = urlsplit(raw)
        scheme = parsed.scheme.casefold()
        if scheme not in {"http", "https"} or not parsed.hostname:
            return None
        host = parsed.hostname.casefold()
        if ":" in host:
            host = f"[{host}]"
        port = parsed.port
        if port and (scheme, port) not in {("http", 80), ("https", 443)}:
            host = f"{host}:{port}"
        path = parsed.path.rstrip("/") or ""
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
        return urlunsplit((scheme, host, path, query, ""))
    except ValueError:
        return None


@dataclass(frozen=True)
class SourceProvenance:
    source_id: str
    content_hash: str
    source_version: str
    source_version_id: str
    original_source_name: str
    original_source_path: str
    url: str | None = None
    doi: str | None = None
    isbn: str | None = None
    edition: str | None = None
    publisher: str | None = None
    license: str | None = None
    rights: str | None = None
    author: str | None = None
    year: int | None = None
    publication_date: str | None = None
    acquisition_date: str | None = None
    reviewer: str | None = None
    review_date: str | None = None
    review_due_date: str | None = None
    evidence_level: str | None = None
    area: str | None = None
    population: str | None = None
    source_type: str | None = None

    @classmethod
    def from_content(cls, content: bytes | str, metadata: dict) -> "SourceProvenance":
        raw_content = content.encode("utf-8") if isinstance(content, str) else content
        content_hash = hashlib.sha256(raw_content).hexdigest()
        doi = _normalize_doi(metadata.get("doi"))
        isbn = _normalize_isbn(metadata.get("isbn"))
        url = _normalize_url(metadata.get("url") or metadata.get("canonical_url"))
        source_key = _text(metadata.get("source_key"))
        original_name = _text(metadata.get("original_source_name") or metadata.get("file_name"))
        original_path = _text(
            metadata.get("original_source_path") or metadata.get("source_file") or original_name
        )
        if not original_name or not original_path:
            raise ValueError("original source name and path are required")
        if doi:
            source_id = f"doi:{doi}"
        elif isbn:
            source_id = f"isbn:{isbn}"
        elif url:
            source_id = f"url:{url}"
        elif source_key:
            normalized_key = source_key.replace("\\", "/").casefold()
            source_id = f"key:{hashlib.sha256(normalized_key.encode()).hexdigest()}"
        else:
            source_key = original_path.replace("\\", "/").strip("./").casefold()
            if metadata.get("identity_scope") == "upload":
                source_key = f"upload:{source_key}:{content_hash}"
            source_id = f"source:{hashlib.sha256(source_key.encode()).hexdigest()}"
        explicit_version = _text(metadata.get("version"))
        values = {field: _text(metadata.get(field)) for field in _OPTIONAL_FIELDS}
        values["publication_date"] = _text(metadata.get("publication_date") or metadata.get("date"))
        raw_year = _text(metadata.get("year"))
        year = int(raw_year) if raw_year and raw_year.lstrip("+-").isdigit() else None
        source_version = explicit_version or f"sha256:{content_hash}"
        version_key = f"{source_id}\0{source_version}\0{content_hash}".encode()
        source_version_id = hashlib.sha256(version_key).hexdigest()
        return cls(
            source_id=source_id,
            content_hash=content_hash,
            source_version=source_version,
            source_version_id=source_version_id,
            original_source_name=original_name,
            original_source_path=original_path,
            url=url,
            doi=doi,
            isbn=isbn,
            year=year if year is not None and 1000 <= year <= 9999 else None,
            **values,
        )

    def payload(self) -> dict:
        return {key: value for key, value in asdict(self).items() if value is not None}
