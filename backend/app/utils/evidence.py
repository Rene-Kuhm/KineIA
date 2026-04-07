from enum import Enum


class EvidenceLevel(str, Enum):
    PROTOCOL = "protocol"  # 🟢 Protocolo oficial / Guía clínica
    BOOK = "book"          # 🔵 Libro de referencia universitario
    PAPER = "paper"        # 🟡 Paper / Investigación publicada
    NOTES = "notes"        # 🟠 Apunte universitario


EVIDENCE_PRIORITY = {
    EvidenceLevel.PROTOCOL: 4,
    EvidenceLevel.BOOK: 3,
    EvidenceLevel.PAPER: 2,
    EvidenceLevel.NOTES: 1,
}

EVIDENCE_EMOJI = {
    EvidenceLevel.PROTOCOL: "🟢",
    EvidenceLevel.BOOK: "🔵",
    EvidenceLevel.PAPER: "🟡",
    EvidenceLevel.NOTES: "🟠",
}


def get_evidence_priority(level: str) -> int:
    try:
        return EVIDENCE_PRIORITY[EvidenceLevel(level)]
    except (ValueError, KeyError):
        return 0


def get_evidence_label(level: str) -> str:
    labels = {
        "protocol": "Protocolo oficial / Guía clínica",
        "book": "Libro de referencia universitario",
        "paper": "Paper / Investigación publicada",
        "notes": "Apunte universitario",
    }
    return labels.get(level, "Fuente no clasificada")
