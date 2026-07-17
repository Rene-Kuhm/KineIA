import re


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
) -> list[dict]:
    """Split text into overlapping chunks, respecting paragraph and header boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    sections = re.split(r"\n(?=#{1,6}(?:[ \t]|\n|$))", text)

    chunks = []
    current_chunk = ""
    current_header = ""
    current_section_heading = None
    current_section_path = None
    section_slots = [None] * 6

    for section in sections:
        # Detect header
        header_match = re.match(r"^(#{1,6})(?:[ \t]+([^\n]*))?(?:\n|$)", section)
        if header_match:
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "header": current_header,
                    "word_count": len(current_chunk.split()),
                    "section_heading": current_section_heading,
                    "section_path": current_section_path,
                })
                current_chunk = ""
            marks, heading = header_match.groups()
            current_header = header_match.group(0).strip()
            safe_heading = (heading or "").strip()
            if (not safe_heading or len(safe_heading) > 200
                    or not all(char.isprintable() for char in safe_heading)):
                safe_heading = None
            level = len(marks) - 1
            section_slots[level:] = [None] * (6 - level)
            section_slots[level] = safe_heading or False
            visible_slots = section_slots[: level + 1]
            valid_locator = False not in visible_slots
            current_section_heading = safe_heading if valid_locator else None
            current_section_path = (
                [part for part in visible_slots if part] if valid_locator else None
            )

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
                        "section_heading": current_section_heading,
                        "section_path": current_section_path,
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
                                "section_heading": current_section_heading,
                                "section_path": current_section_path,
                            })
                    current_chunk = ""

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "header": current_header,
            "word_count": len(current_chunk.split()),
            "section_heading": current_section_heading,
            "section_path": current_section_path,
        })

    return chunks
