import re
from pathlib import Path


def extract_markdown(file_path: str) -> dict:
    """Extract text and metadata from a Markdown file with YAML frontmatter."""
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")

    metadata = {}
    body = content

    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        body = content[frontmatter_match.end():]

        for line in frontmatter.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value.isdigit():
                    value = int(value)
                metadata[key] = value

    return {
        "text": body.strip(),
        "metadata": metadata,
        "source_file": str(path),
        "file_name": path.name,
    }
