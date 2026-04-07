import re


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Split text into overlapping chunks, respecting paragraph and header boundaries."""
    # Split by headers and double newlines first
    sections = re.split(r"\n(?=#{1,4}\s)", text)

    chunks = []
    current_chunk = ""
    current_header = ""

    for section in sections:
        # Detect header
        header_match = re.match(r"^(#{1,4}\s+.+)\n", section)
        if header_match:
            current_header = header_match.group(1).strip()

        paragraphs = section.split("\n\n")

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            words = para.split()
            para_word_count = len(words)

            if len(current_chunk.split()) + para_word_count <= chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk.strip(),
                        "header": current_header,
                        "word_count": len(current_chunk.split()),
                    })

                # Handle overlap
                if chunk_overlap > 0 and current_chunk:
                    overlap_words = current_chunk.split()[-chunk_overlap:]
                    current_chunk = " ".join(overlap_words) + "\n\n" + para
                else:
                    current_chunk = para

                # If single paragraph exceeds chunk_size, split it
                if len(current_chunk.split()) > chunk_size:
                    words = current_chunk.split()
                    for i in range(0, len(words), chunk_size - chunk_overlap):
                        chunk_words = words[i : i + chunk_size]
                        if chunk_words:
                            chunks.append({
                                "text": " ".join(chunk_words),
                                "header": current_header,
                                "word_count": len(chunk_words),
                            })
                    current_chunk = ""

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "header": current_header,
            "word_count": len(current_chunk.split()),
        })

    return chunks
