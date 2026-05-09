import pytest


@pytest.fixture
def sample_text():
    return (
        "# Introducción\n\n"
        "La kinesiología es la ciencia del movimiento humano.\n\n"
        "## Biomecánica\n\n"
        "Estudia las fuerzas internas y externas que actúan sobre el cuerpo.\n\n"
        "## Evaluación\n\n"
        "La evaluación kinesiológica incluye anamnesis, inspección, palpación y pruebas funcionales.\n\n"
        "Se deben considerar los antecedentes del paciente para un diagnóstico adecuado.\n\n"
    )


@pytest.fixture
def sample_doc_metadata():
    return {
        "title": "Manual de Kinesiología",
        "source_type": "book",
        "area": "kinesiologia",
        "university": "UBA",
        "author": "Dr. Pérez",
        "year": 2020,
        "evidence_level": "book",
    }


@pytest.fixture
def sample_qdrant_points():
    """Simulate Qdrant search results."""
    from unittest.mock import MagicMock

    points = []
    for i in range(5):
        point = MagicMock()
        point.id = f"point-{i}"
        point.score = 0.95 - i * 0.05
        point.payload = {
            "text": f"Documento {i} sobre kinesiología aplicada.",
            "title": f"Fuente {i}",
            "source_type": "book" if i < 2 else "paper",
            "area": "kinesiologia" if i < 3 else "traumatologia",
            "evidence_level": "book" if i < 2 else "paper",
            "university": "UBA",
            "author": f"Autor {i}",
            "year": 2020 + i,
        }
        points.append(point)
    return points
