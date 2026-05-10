#!/usr/bin/env python3
"""
KineIA OSCE Evaluation Script
==============================
Evalúa KineIA contra el benchmark de preguntas usando el marco OSCE de 32 ejes.

Uso:
    python scripts/evaluate.py --benchmark docs/benchmark-preguntas.md --output resultados.csv
    python scripts/evaluate.py --benchmark docs/benchmark-preguntas.md --area traumatologia --mode profesional
    python scripts/evaluate.py --benchmark docs/benchmark-preguntas.md --limit 10 --output resultados.csv --verbose

Requisitos:
    - Python 3.10+
    - requests
    - KineIA backend corriendo (configurable con --api-url)
"""

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================================
# Configuración
# ============================================================================

DEFAULT_API_URL = "http://localhost:8000/api/v1"
DEFAULT_BENCHMARK = "docs/benchmark-preguntas.md"
DEFAULT_OUTPUT = "resultados_osce.csv"

# 32 Ejes OSCE con sus pesos y categorías
OSCE_AXES = {
    # Anamnesis / Recolección de Datos (6 ejes, 15%)
    "H1": {
        "categoria": "Anamnesis",
        "nombre": "Pertinencia de preguntas",
        "peso": 0.15 / 6,
    },
    "H2": {
        "categoria": "Anamnesis",
        "nombre": "Completitud de la anamnesis",
        "peso": 0.15 / 6,
    },
    "H3": {
        "categoria": "Anamnesis",
        "nombre": "Organización del interrogatorio",
        "peso": 0.15 / 6,
    },
    "H4": {
        "categoria": "Anamnesis",
        "nombre": "Identificación de señales de alarma",
        "peso": 0.15 / 6,
    },
    "H5": {
        "categoria": "Anamnesis",
        "nombre": "Contextualización del paciente",
        "peso": 0.15 / 6,
    },
    "H6": {
        "categoria": "Anamnesis",
        "nombre": "Uso de escalas validadas",
        "peso": 0.15 / 6,
    },
    # Diagnóstico / Evaluación (8 ejes, 30%)
    "D1": {
        "categoria": "Diagnóstico",
        "nombre": "Precisión diagnóstica",
        "peso": 0.30 / 8,
    },
    "D2": {
        "categoria": "Diagnóstico",
        "nombre": "Diagnóstico diferencial",
        "peso": 0.30 / 8,
    },
    "D3": {
        "categoria": "Diagnóstico",
        "nombre": "Razonamiento basado en evidencia",
        "peso": 0.30 / 8,
    },
    "D4": {
        "categoria": "Diagnóstico",
        "nombre": "Relación anatomofuncional",
        "peso": 0.30 / 8,
    },
    "D5": {
        "categoria": "Diagnóstico",
        "nombre": "Interpretación de estudios complementarios",
        "peso": 0.30 / 8,
    },
    "D6": {
        "categoria": "Diagnóstico",
        "nombre": "Clasificación de gravedad",
        "peso": 0.30 / 8,
    },
    "D7": {
        "categoria": "Diagnóstico",
        "nombre": "Valoración funcional",
        "peso": 0.30 / 8,
    },
    "D8": {
        "categoria": "Diagnóstico",
        "nombre": "Pronóstico funcional",
        "peso": 0.30 / 8,
    },
    # Manejo / Tratamiento (8 ejes, 30%)
    "M1": {
        "categoria": "Manejo",
        "nombre": "Adherencia a protocolos",
        "peso": 0.30 / 8,
    },
    "M2": {
        "categoria": "Manejo",
        "nombre": "Seguridad del paciente",
        "peso": 0.30 / 8,
    },
    "M3": {
        "categoria": "Manejo",
        "nombre": "Personalización del tratamiento",
        "peso": 0.30 / 8,
    },
    "M4": {
        "categoria": "Manejo",
        "nombre": "Progresión de cargas",
        "peso": 0.30 / 8,
    },
    "M5": {
        "categoria": "Manejo",
        "nombre": "Dosificación de ejercicios",
        "peso": 0.30 / 8,
    },
    "M6": {
        "categoria": "Manejo",
        "nombre": "Uso de agentes físicos",
        "peso": 0.30 / 8,
    },
    "M7": {
        "categoria": "Manejo",
        "nombre": "Educación terapéutica",
        "peso": 0.30 / 8,
    },
    "M8": {
        "categoria": "Manejo",
        "nombre": "Criterios de alta",
        "peso": 0.30 / 8,
    },
    # Comunicación (6 ejes, 15%)
    "C1": {
        "categoria": "Comunicación",
        "nombre": "Claridad del lenguaje",
        "peso": 0.15 / 6,
    },
    "C2": {
        "categoria": "Comunicación",
        "nombre": "Empatía y rapport",
        "peso": 0.15 / 6,
    },
    "C3": {
        "categoria": "Comunicación",
        "nombre": "Valor pedagógico",
        "peso": 0.15 / 6,
    },
    "C4": {
        "categoria": "Comunicación",
        "nombre": "Estructura de la respuesta",
        "peso": 0.15 / 6,
    },
    "C5": {
        "categoria": "Comunicación",
        "nombre": "Manejo del desconocimiento",
        "peso": 0.15 / 6,
    },
    "C6": {
        "categoria": "Comunicación",
        "nombre": "Redirección a fuentes",
        "peso": 0.15 / 6,
    },
    # Integración de Conocimiento (4 ejes, 10%)
    "K1": {
        "categoria": "Integración",
        "nombre": "Citación de fuentes",
        "peso": 0.10 / 4,
    },
    "K2": {
        "categoria": "Integración",
        "nombre": "Niveles de evidencia",
        "peso": 0.10 / 4,
    },
    "K3": {
        "categoria": "Integración",
        "nombre": "Contexto argentino",
        "peso": 0.10 / 4,
    },
    "K4": {
        "categoria": "Integración",
        "nombre": "Actualización del conocimiento",
        "peso": 0.10 / 4,
    },
}


# ============================================================================
# Modelos de datos
# ============================================================================


@dataclass
class PreguntaBenchmark:
    """Una pregunta del benchmark con su respuesta esperada."""

    id: str
    area: str
    tema: str
    dificultad: str
    modo: str
    pregunta: str
    respuesta_esperada: str
    ejes_primarios: list[str] = field(default_factory=list)
    ejes_secundarios: list[str] = field(default_factory=list)
    fuentes: list[str] = field(default_factory=list)


@dataclass
class RespuestaKineIA:
    """Respuesta obtenida de la API de KineIA."""

    pregunta_id: str
    query: str
    answer: str
    sources: list[dict[str, Any]]
    response_time_ms: int
    mode: str
    error: str | None = None


@dataclass
class ResultadoEvaluacion:
    """Resultado completo de la evaluación OSCE para una pregunta."""

    pregunta_id: str
    area: str
    tema: str
    dificultad: str
    modo: str
    scores: dict[str, int]  # eje -> puntaje 1-5
    score_total: float  # ponderado 0-160
    score_anamnesis: float
    score_diagnostico: float
    score_manejo: float
    score_comunicacion: float
    score_integracion: float
    response_time_ms: int
    sources_count: int
    error: str | None = None


# ============================================================================
# Parser del benchmark
# ============================================================================


def parse_benchmark(archivo: str) -> list[PreguntaBenchmark]:
    """
    Parsea el archivo benchmark-preguntas.md extrayendo preguntas completas.

    Reconoce preguntas en el formato:
        ### Pregunta #XXX
        **Área**: ...
        **Tema**: ...
        ...
        **Respuesta esperada**: ...
        **Fuentes de referencia**: ...
        **Ejes OSCE a evaluar**: ...
    """
    path = Path(archivo)
    if not path.exists():
        print(f"ERROR: Archivo de benchmark no encontrado: {archivo}")
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    preguntas: list[PreguntaBenchmark] = []

    # Buscar cada bloque de pregunta
    import re

    # Patrón: encuentra desde "### Pregunta #XXX" hasta el siguiente "### Pregunta" o "---"
    bloques = re.split(r"\n(?=### Pregunta #)", content)

    for bloque in bloques:
        if not bloque.strip().startswith("### Pregunta #"):
            continue

        # Extraer campos con regex
        def extraer(campo: str, texto: str) -> str:
            patron = rf"\*\*{campo}\*\*:\s*(.+?)(?:\n|$)"
            match = re.search(patron, texto)
            return match.group(1).strip() if match else ""

        def extraer_multilinea(campo: str, texto: str) -> str:
            """Extrae campo cuyo valor puede ocupar múltiples líneas."""
            patron = rf"\*\*{campo}\*\*:\s*(.+?)(?=\n\*\*|$)"
            match = re.search(patron, texto, re.DOTALL)
            return match.group(1).strip() if match else ""

        id_match = re.search(r"### Pregunta #(\d+)", bloque)
        pregunta_id = id_match.group(1) if id_match else "???"

        area = extraer("Área", bloque)
        tema = extraer("Tema", bloque)
        dificultad = extraer("Dificultad", bloque)
        modo = extraer("Modo", bloque)

        # La pregunta y respuesta esperada pueden ser multilínea
        pregunta_texto = extraer_multilinea("Pregunta", bloque)
        respuesta_esperada = extraer_multilinea("Respuesta esperada", bloque)

        # Fuentes
        fuentes_str = extraer("Fuentes de referencia", bloque)
        fuentes = [f.strip() for f in fuentes_str.replace("`", "").split(",") if f.strip()]

        # Ejes
        ejes_str = extraer("Ejes OSCE a evaluar", bloque)
        ejes_primarios = []
        ejes_secundarios = []
        if "Primarios:" in ejes_str:
            partes_prim = ejes_str.split("Primarios:")[1].split("Secundarios:")[0]
            ejes_primarios = [e.strip() for e in partes_prim.replace("-", "").split(",") if e.strip()]
        if "Secundarios:" in ejes_str:
            partes_sec = ejes_str.split("Secundarios:")[1]
            ejes_secundarios = [e.strip() for e in partes_sec.replace("-", "").split(",") if e.strip()]

        if not pregunta_texto or not respuesta_esperada:
            continue  # Skip preguntas template sin contenido

        preguntas.append(
            PreguntaBenchmark(
                id=pregunta_id,
                area=area,
                tema=tema,
                dificultad=dificultad,
                modo=modo,
                pregunta=pregunta_texto,
                respuesta_esperada=respuesta_esperada,
                ejes_primarios=ejes_primarios,
                ejes_secundarios=ejes_secundarios,
                fuentes=fuentes,
            )
        )

    return preguntas


# ============================================================================
# Cliente de API KineIA
# ============================================================================


class KineIAClient:
    """Cliente HTTP para la API de KineIA."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = None

    @property
    def session(self):
        if self._session is None:
            import requests

            self._session = requests.Session()
            self._session.headers.update(
                {"Content-Type": "application/json", "Accept": "application/json"}
            )
        return self._session

    def health_check(self) -> bool:
        """Verifica que la API de KineIA esté respondiendo."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def send_query(
        self, query: str, mode: str = "professional", area: str | None = None
    ) -> RespuestaKineIA:
        """
        Envía una consulta al endpoint de chat de KineIA.

        POST /api/v1/chat
        {
            "query": "...",
            "mode": "profesional|estudiante",
            "area": null
        }
        """
        try:
            payload = {"query": query, "mode": mode}
            if area:
                payload["area"] = area

            start = time.time()
            resp = self.session.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=self.timeout,
            )
            elapsed_ms = int((time.time() - start) * 1000)

            if resp.status_code != 200:
                return RespuestaKineIA(
                    pregunta_id="",
                    query=query,
                    answer="",
                    sources=[],
                    response_time_ms=elapsed_ms,
                    mode=mode,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            data = resp.json()
            # La API responde: {"status": "success", "data": {"answer": "...", "sources": [...], ...}}
            result = data.get("data", data)

            return RespuestaKineIA(
                pregunta_id="",
                query=query,
                answer=result.get("answer", ""),
                sources=result.get("sources", []),
                response_time_ms=result.get("response_time_ms", elapsed_ms),
                mode=mode,
            )

        except Exception as e:
            return RespuestaKineIA(
                pregunta_id="",
                query=query,
                answer="",
                sources=[],
                response_time_ms=0,
                mode=mode,
                error=str(e),
            )


# ============================================================================
# Motor de puntuación OSCE
# ============================================================================


class OSCEScorer:
    """
    Motor de puntuación OSCE que evalúa respuestas de KineIA contra
    respuestas esperadas del benchmark.

    Utiliza heurísticas basadas en contenido para asignar puntajes
    automatizados por eje (1-5). Para evaluación de alta precisión,
    usar panel de expertos (ver docs/protocolo-panel-expertos.md).
    """

    # Palabras clave por eje para puntuación heurística
    KEYWORDS: dict[str, list[str]] = {
        # Anamnesis
        "H1": [
            "evaluación",
            "antecedentes",
            "mecanismo de lesión",
            "exploración",
            "interrogatorio",
        ],
        "H2": [
            "anamnesis",
            "antecedentes personales",
            "tratamientos previos",
            "medicación",
            "comorbilidades",
        ],
        "H3": ["primero", "luego", "finalmente", "secuencia", "paso"],
        "H4": [
            "bandera roja",
            "red flag",
            "señal de alarma",
            "derivación urgente",
            "contraindicación",
            "signo de gravedad",
        ],
        "H5": ["edad", "actividad", "deporte", "ocupación", "nivel funcional", "perfil"],
        "H6": [
            "EVA",
            "Daniels",
            "FIM",
            "Barthel",
            "escala",
            "Barthel",
            "Berg",
            "test de",
            "índice de",
        ],
        # Diagnóstico
        "D1": [
            "diagnóstico",
            "compatible con",
            "sugiere",
            "corresponde a",
            "clasifica como",
        ],
        "D2": [
            "diagnóstico diferencial",
            "descartar",
            "podría ser",
            "vs",
            "versus",
            "alternativas",
            "confundir",
        ],
        "D3": [
            "evidencia",
            "estudio",
            "ensayo clínico",
            "guía",
            "recomendación",
            "según",
            "de acuerdo a",
        ],
        "D4": [
            "anatomía",
            "biomecánica",
            "fisiología articular",
            "músculo",
            "inserción",
            "origen",
            "inervación",
            "articulación",
        ],
        "D5": [
            "radiografía",
            "resonancia",
            "ecografía",
            "espirometría",
            "gasometría",
            "EMG",
            "estudio complementario",
            "FEV1",
            "PaO2",
        ],
        "D6": ["escala", "clasificación", "grado", "nivel", "severidad", "estadio", "GOLD", "ASIA"],
        "D7": [
            "AVD",
            "actividades de la vida diaria",
            "funcionalidad",
            "independencia",
            "marcha",
            "transferencia",
        ],
        "D8": [
            "pronóstico",
            "recuperación",
            "plazo",
            "semanas",
            "meses",
            "factores pronóstico",
            "retorno",
        ],
        # Manejo
        "M1": [
            "protocolo",
            "guía clínica",
            "INAREPs",
            "SATI",
            "GOLD",
            "consenso",
            "recomendación",
            "según",
        ],
        "M2": [
            "contraindicación",
            "precaución",
            "cuidado",
            "riesgo",
            "seguridad",
            "no se debe",
            "evitar",
            "derivar",
        ],
        "M3": [
            "personalizado",
            "individualizado",
            "adaptado",
            "según el paciente",
            "considerar",
            "dependiendo",
        ],
        "M4": ["fase", "semana", "progresión", "avance", "criterio", "etapa", "cuando"],
        "M5": [
            "series",
            "repeticiones",
            "intensidad",
            "frecuencia",
            "RM",
            "%",
            "segundos",
            "minutos",
        ],
        "M6": [
            "electroterapia",
            "TENS",
            "ultrasonido",
            "magnetoterapia",
            "láser",
            "crioterapia",
            "hidroterapia",
            "onda de choque",
            "Hz",
            "W/cm2",
        ],
        "M7": [
            "educación",
            "explicar",
            "informar",
            "enseñar",
            "autocuidado",
            "recomendaciones",
            "pautas",
        ],
        "M8": [
            "alta",
            "criterio de alta",
            "return to play",
            "return to sport",
            "retorno deportivo",
            "fin del tratamiento",
            "objetivo final",
        ],
        # Comunicación
        "C1": ["claro", "entendible", "técnico", "sencillo", "término médico"],
        "C2": [
            "excelente pregunta",
            "muy buena consulta",
            "entiendo",
            "es común",
            "importante",
            "vamos",
        ],
        "C3": [
            "ejemplo",
            "imagina",
            "recordá",
            "analogía",
            "como si",
            "pensá en",
            "dato",
        ],
        "C4": ["##", "###", "- ", "* ", "1.", "tabla", "resumen", "en conclusión"],
        "C5": [
            "no tengo información",
            "no encontré",
            "mi conocimiento",
            "no está en mi base",
            "fuera de mi alcance",
            "te sugiero consultar",
        ],
        "C6": [
            "consulte a",
            "derive a",
            "recomiendo consultar",
            "especialista",
            "médico",
            "fuente adicional",
        ],
        # Integración
        "K1": [
            "fuente",
            "referencia",
            "bibliografía",
            "citado en",
            "según",
            "basado en",
            "tomado de",
        ],
        "K2": ["nivel de evidencia", "protocolo oficial", "libro de referencia", "paper", "apunte"],
        "K3": [
            "Argentina",
            "argentino",
            "INAREPs",
            "SATI",
            "UNC",
            "UBA",
            "UNSL",
            "Favaloro",
            "ministerio",
            "nacional",
        ],
        "K4": ["actual", "reciente", "2024", "2023", "2025", "última", "vigente", "actualizado"],
    }

    def score_answer(
        self,
        pregunta: PreguntaBenchmark,
        respuesta: RespuestaKineIA,
    ) -> ResultadoEvaluacion:
        """
        Evalúa la respuesta de KineIA contra la pregunta del benchmark.

        Retorna un ResultadoEvaluacion con puntajes por eje 1-5
        y puntajes compuestos.
        """
        if respuesta.error:
            return ResultadoEvaluacion(
                pregunta_id=pregunta.id,
                area=pregunta.area,
                tema=pregunta.tema,
                dificultad=pregunta.dificultad,
                modo=pregunta.modo,
                scores={},
                score_total=0.0,
                score_anamnesis=0.0,
                score_diagnostico=0.0,
                score_manejo=0.0,
                score_comunicacion=0.0,
                score_integracion=0.0,
                response_time_ms=respuesta.response_time_ms,
                sources_count=0,
                error=respuesta.error,
            )

        answer_lower = respuesta.answer.lower()
        expected_lower = pregunta.respuesta_esperada.lower()

        # Calcular puntajes heurísticos por eje
        scores: dict[str, int] = {}
        for eje_code, eje_info in OSCE_AXES.items():
            is_primary = eje_code in pregunta.ejes_primarios
            is_secondary = eje_code in pregunta.ejes_secundarios

            score = self._score_axis(
                eje_code,
                answer_lower,
                expected_lower,
                is_primary=is_primary,
                is_secondary=is_secondary,
            )
            scores[eje_code] = score

        # Calcular puntajes compuestos ponderados
        def cat_score(cat: str) -> float:
            total = 0.0
            for eje_code, eje_info in OSCE_AXES.items():
                if eje_info["categoria"] == cat:
                    raw = scores.get(eje_code, 0)
                    # Normalizar: puntaje bruto (1-5) multiplicado por peso del eje dentro de la categoría
                    # Luego escalamos a 0-100% del máximo de la categoría
                    total += raw * eje_info["peso"]
            # Convertir a escala 0-100% de la categoría
            cat_max = sum(
                e["peso"] * 5 for e in OSCE_AXES.values() if e["categoria"] == cat
            )
            return (total / cat_max * 100) if cat_max > 0 else 0.0

        score_total = sum(
            scores.get(e, 0) * OSCE_AXES[e]["peso"] for e in OSCE_AXES
        )
        # Normalizar a 160 (32 ejes × 5 puntos)
        score_total = (score_total / 0.20) * 160  # 0.20 = suma de pesos = 1.0, 5 puntos máx por eje

        return ResultadoEvaluacion(
            pregunta_id=pregunta.id,
            area=pregunta.area,
            tema=pregunta.tema,
            dificultad=pregunta.dificultad,
            modo=pregunta.modo,
            scores=scores,
            score_total=min(score_total, 160.0),
            score_anamnesis=cat_score("Anamnesis"),
            score_diagnostico=cat_score("Diagnóstico"),
            score_manejo=cat_score("Manejo"),
            score_comunicacion=cat_score("Comunicación"),
            score_integracion=cat_score("Integración"),
            response_time_ms=respuesta.response_time_ms,
            sources_count=len(respuesta.sources),
        )

    def _score_axis(
        self,
        eje: str,
        answer: str,
        expected: str,
        is_primary: bool = False,
        is_secondary: bool = False,
    ) -> int:
        """
        Asigna puntaje 1-5 para un eje basado en heurísticas de contenido.

        La puntuación combina:
        - Presencia de palabras clave del eje
        - Solapamiento de contenido con la respuesta esperada
        - Relevancia del eje para la pregunta (primario/secundario)
        - Longitud y estructura de la respuesta
        """
        keywords = self.KEYWORDS.get(eje, [])
        if not keywords:
            return 3  # Puntaje neutral si no hay keywords definidas

        # Contar keywords presentes
        hits = sum(1 for kw in keywords if kw.lower() in answer)
        expected_hits = sum(1 for kw in keywords if kw.lower() in expected)

        # Si la respuesta esperada no cubre este eje, no penalizar fuerte
        if expected_hits == 0:
            return 2 if is_primary else 3

        # Calcular ratio de cobertura
        coverage = hits / len(keywords) if keywords else 0

        # Ajustar por relevancia
        if is_primary:
            base = 2  # Se espera buena cobertura en ejes primarios
        elif is_secondary:
            base = 1
        else:
            base = 0

        # Mapping heurístico a puntaje 1-5
        if coverage >= 0.5:
            score = 4 + base
        elif coverage >= 0.3:
            score = 3 + base
        elif coverage >= 0.1:
            score = 2 + base
        else:
            score = 1 + base

        # Limitar a rango 1-5
        return max(1, min(5, score))


# ============================================================================
# Generación de reportes
# ============================================================================


def generate_csv_report(resultados: list[ResultadoEvaluacion], output_path: str) -> None:
    """Genera un archivo CSV con los resultados detallados por pregunta."""
    fieldnames = [
        "pregunta_id",
        "area",
        "tema",
        "dificultad",
        "modo",
        "score_total",
        "score_anamnesis",
        "score_diagnostico",
        "score_manejo",
        "score_comunicacion",
        "score_integracion",
        "response_time_ms",
        "sources_count",
        "error",
        # Todos los ejes individuales
        *[f"score_{e}" for e in sorted(OSCE_AXES.keys())],
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for r in resultados:
            row = {
                "pregunta_id": r.pregunta_id,
                "area": r.area,
                "tema": r.tema,
                "dificultad": r.dificultad,
                "modo": r.modo,
                "score_total": round(r.score_total, 1),
                "score_anamnesis": round(r.score_anamnesis, 1),
                "score_diagnostico": round(r.score_diagnostico, 1),
                "score_manejo": round(r.score_manejo, 1),
                "score_comunicacion": round(r.score_comunicacion, 1),
                "score_integracion": round(r.score_integracion, 1),
                "response_time_ms": r.response_time_ms,
                "sources_count": r.sources_count,
                "error": r.error or "",
            }
            for eje in sorted(OSCE_AXES.keys()):
                row[f"score_{eje}"] = r.scores.get(eje, 0)

            writer.writerow(row)

    print(f"\n✅ Reporte CSV generado: {output_path}")


def print_summary(resultados: list[ResultadoEvaluacion], verbose: bool = False) -> None:
    """Imprime un resumen de la evaluación en consola."""
    if not resultados:
        print("❌ No hay resultados para mostrar.")
        return

    validos = [r for r in resultados if r.error is None]
    errores = [r for r in resultados if r.error is not None]

    print("\n" + "=" * 70)
    print("  KineIA OSCE Evaluation — Resultados")
    print("=" * 70)
    print(f"  Fecha:        {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Preguntas:    {len(resultados)} total")
    print(f"  Completadas:  {len(validos)} ✅")
    print(f"  Con error:    {len(errores)} ❌")
    print("=" * 70)

    if not validos:
        print("\n⚠️  Todas las consultas fallaron. Verificá que KineIA esté corriendo.")
        for e in errores:
            print(f"  - Pregunta #{e.pregunta_id}: {e.error}")
        return

    # Estadísticas globales
    scores_totales = [r.score_total for r in validos]
    avg_score = sum(scores_totales) / len(scores_totales)

    print(f"\n  📊 Score Global Promedio: {avg_score:.1f} / 160")

    # Interpretación
    if avg_score >= 145:
        nivel = "Sobresaliente ⭐"
    elif avg_score >= 128:
        nivel = "Muy Bueno ✅"
    elif avg_score >= 96:
        nivel = "Bueno ✓"
    elif avg_score >= 64:
        nivel = "Regular ⚠️"
    else:
        nivel = "Insuficiente ❌"

    print(f"  🏆 Nivel: {nivel}")

    # Promedios por categoría
    print("\n  📋 Scores por Categoría:")
    for cat in ["Anamnesis", "Diagnóstico", "Manejo", "Comunicación", "Integración"]:
        attr = f"score_{cat.lower().replace('ó', 'o').replace('í', 'i')}"
        cat_scores = [getattr(r, attr, 0) for r in validos]
        cat_avg = sum(cat_scores) / len(cat_scores)
        bar = "█" * int(cat_avg / 5) + "░" * (20 - int(cat_avg / 5))
        print(f"    {cat:<15} {bar} {cat_avg:.1f}%")

    # Tiempo de respuesta promedio
    avg_time = sum(r.response_time_ms for r in validos) / len(validos)
    print(f"\n  ⏱️  Tiempo de respuesta promedio: {avg_time:.0f} ms")

    # Fuentes promedio
    avg_sources = sum(r.sources_count for r in validos) / len(validos)
    print(f"  📚 Fuentes promedio por respuesta: {avg_sources:.1f}")

    # Top 5 y Bottom 5
    if verbose:
        print("\n  🔝 Top 5 preguntas con mejor score:")
        sorted_r = sorted(validos, key=lambda r: r.score_total, reverse=True)
        for r in sorted_r[:5]:
            print(f"    #{r.pregunta_id} [{r.area}] {r.tema}: {r.score_total:.1f}")

        print("\n  🔻 Bottom 5 preguntas con peor score:")
        for r in sorted_r[-5:]:
            print(f"    #{r.pregunta_id} [{r.area}] {r.tema}: {r.score_total:.1f}")

    # Resultados por área
    print("\n  📂 Scores por Área:")
    areas: dict[str, list[float]] = {}
    for r in validos:
        areas.setdefault(r.area, []).append(r.score_total)

    for area, scores_list in sorted(areas.items()):
        area_avg = sum(scores_list) / len(scores_list)
        print(f"    {area:<20} {area_avg:.1f} / 160  (n={len(scores_list)})")

    # Resultados por modo
    modos: dict[str, list[float]] = {}
    for r in validos:
        modos.setdefault(r.modo, []).append(r.score_total)

    if len(modos) > 1:
        print("\n  🎓 Scores por Modo:")
        for modo, scores_list in sorted(modos.items()):
            modo_avg = sum(scores_list) / len(scores_list)
            print(f"    {modo:<20} {modo_avg:.1f} / 160  (n={len(scores_list)})")

    # Ejes con mejor y peor desempeño
    print("\n  📐 Desempeño por Eje OSCE:")
    eje_scores: dict[str, list[int]] = {}
    for r in validos:
        for eje, score in r.scores.items():
            eje_scores.setdefault(eje, []).append(score)

    eje_promedios = {
        eje: sum(scores) / len(scores) for eje, scores in eje_scores.items()
    }
    sorted_ejes = sorted(eje_promedios.items(), key=lambda x: x[1], reverse=True)

    print("    Top 5 ejes:")
    for eje, avg in sorted_ejes[:5]:
        nombre = OSCE_AXES[eje]["nombre"]
        print(f"      {eje} {nombre:<40} {avg:.1f} / 5")
    print("    Bottom 5 ejes:")
    for eje, avg in sorted_ejes[-5:]:
        nombre = OSCE_AXES[eje]["nombre"]
        print(f"      {eje} {nombre:<40} {avg:.1f} / 5")

    print("\n" + "=" * 70)


# ============================================================================
# Punto de entrada principal
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="KineIA OSCE Evaluation — Evalúa KineIA contra el benchmark de preguntas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/evaluate.py
  python scripts/evaluate.py --area traumatologia
  python scripts/evaluate.py --mode profesional --limit 5
  python scripts/evaluate.py --api-url http://192.168.1.100:8000/api/v1
  python scripts/evaluate.py --verbose --output mi_eval.csv
        """,
    )

    parser.add_argument(
        "--benchmark",
        default=DEFAULT_BENCHMARK,
        help=f"Ruta al archivo benchmark (default: {DEFAULT_BENCHMARK})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Archivo CSV de salida (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"URL base de la API de KineIA (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--area",
        default=None,
        help="Filtrar por área (ej: traumatologia, neurologia, respiratorio, deporte, uci, pediatria, columna)",
    )
    parser.add_argument(
        "--modo",
        default=None,
        help="Filtrar por modo (estudiante, profesional)",
    )
    parser.add_argument(
        "--dificultad",
        default=None,
        help="Filtrar por dificultad (basico, intermedio, avanzado)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limitar número de preguntas a evaluar",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay entre consultas en segundos (default: 1.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar resultados detallados (top/bottom preguntas)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo cargar benchmark sin consultar API (para testing)",
    )

    args = parser.parse_args()

    # 1. Cargar benchmark
    print(f"📖 Cargando benchmark: {args.benchmark}")
    preguntas = parse_benchmark(args.benchmark)
    print(f"   {len(preguntas)} preguntas cargadas")

    if not preguntas:
        print("❌ No se encontraron preguntas completas en el benchmark.")
        sys.exit(1)

    # 2. Aplicar filtros
    if args.area:
        preguntas = [p for p in preguntas if p.area.lower() == args.area.lower()]
        print(f"   🔍 Filtro área={args.area}: {len(preguntas)} preguntas restantes")

    if args.modo:
        preguntas = [p for p in preguntas if p.modo.lower() == args.modo.lower()]
        print(f"   🔍 Filtro modo={args.modo}: {len(preguntas)} preguntas restantes")

    if args.dificultad:
        preguntas = [
            p for p in preguntas if p.dificultad.lower() == args.dificultad.lower()
        ]
        print(f"   🔍 Filtro dificultad={args.dificultad}: {len(preguntas)} preguntas restantes")

    if args.limit:
        preguntas = preguntas[: args.limit]
        print(f"   🔍 Limit={args.limit}: {len(preguntas)} preguntas seleccionadas")

    if not preguntas:
        print("❌ Ninguna pregunta coincide con los filtros aplicados.")
        sys.exit(1)

    # 3. Verificar API (si no es dry-run)
    if not args.dry_run:
        print(f"\n🔌 Conectando a KineIA API: {args.api_url}")
        client = KineIAClient(args.api_url)

        if not client.health_check():
            print(
                f"❌ No se pudo conectar a {args.api_url}/health. "
                f"¿Está corriendo KineIA? Usá --dry-run para probar sin API."
            )
            sys.exit(1)
        print("   ✅ API responde correctamente")
    else:
        print("\n🔌 Modo dry-run: no se consultará la API")
        client = None

    # 4. Ejecutar evaluación
    print(f"\n🚀 Iniciando evaluación de {len(preguntas)} preguntas...\n")
    resultados: list[ResultadoEvaluacion] = []
    scorer = OSCEScorer()

    for i, pregunta in enumerate(preguntas, 1):
        print(f"  [{i}/{len(preguntas)}] #{pregunta.id} — {pregunta.tema} ({pregunta.area}, {pregunta.modo})")

        if args.dry_run:
            # Simular respuesta vacía
            respuesta = RespuestaKineIA(
                pregunta_id=pregunta.id,
                query=pregunta.pregunta,
                answer="[DRY RUN] Respuesta simulada",
                sources=[],
                response_time_ms=0,
                mode=pregunta.modo,
            )
        else:
            respuesta = client.send_query(
                query=pregunta.pregunta,
                mode=pregunta.modo,
                area=pregunta.area,
            )
            respuesta.pregunta_id = pregunta.id

            if respuesta.error:
                print(f"      ❌ Error: {respuesta.error}")
            else:
                print(f"      ✅ {respuesta.response_time_ms}ms | {len(respuesta.sources)} fuentes")

        # Evaluar respuesta
        resultado = scorer.score_answer(pregunta, respuesta)
        resultados.append(resultado)

        # Delay entre consultas
        if not args.dry_run and i < len(preguntas):
            time.sleep(args.delay)

    # 5. Generar reportes
    print_summary(resultados, verbose=args.verbose)
    generate_csv_report(resultados, args.output)

    # 6. Guardar resultados también como JSON para trazabilidad
    json_path = Path(args.output).with_suffix(".json")
    _save_json(resultados, json_path)

    print(f"✅ Evaluación completa. {len(resultados)} preguntas evaluadas.")


def _save_json(resultados: list[ResultadoEvaluacion], path: Path) -> None:
    """Guarda resultados en formato JSON para procesamiento posterior."""
    data = {
        "fecha": datetime.now().isoformat(),
        "total_preguntas": len(resultados),
        "resultados": [
            {
                "pregunta_id": r.pregunta_id,
                "area": r.area,
                "tema": r.tema,
                "dificultad": r.dificultad,
                "modo": r.modo,
                "score_total": round(r.score_total, 1),
                "scores_categoria": {
                    "anamnesis": round(r.score_anamnesis, 1),
                    "diagnostico": round(r.score_diagnostico, 1),
                    "manejo": round(r.score_manejo, 1),
                    "comunicacion": round(r.score_comunicacion, 1),
                    "integracion": round(r.score_integracion, 1),
                },
                "scores_ejes": r.scores,
                "response_time_ms": r.response_time_ms,
                "sources_count": r.sources_count,
                "error": r.error,
            }
            for r in resultados
        ],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📄 Reporte JSON generado: {path}")


if __name__ == "__main__":
    main()
