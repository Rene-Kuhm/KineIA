#!/usr/bin/env python3
"""
KineIA OSCE Evaluation Script

Runs the KineIA agent against a benchmark dataset of kinesiology Q&A pairs,
comparing responses against expected answers and scoring OSCE axes.

Usage:
  python scripts/evaluate.py                          # all questions
  python scripts/evaluate.py --area traumatologia     # filter by area
  python scripts/evaluate.py --mode professional      # filter by mode
  python scripts/evaluate.py --limit 10               # first 10 questions only
  python scripts/evaluate.py --api http://localhost:8000/api/v1  # custom API
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

DEFAULT_API = "http://localhost:8000/api/v1"
BENCHMARK_DIR = Path(__file__).parent.parent / "docs"
OUTPUT_DIR = Path(__file__).parent.parent / "evaluations"

# OSCE evaluation axes adapted for kinesiology
OSCE_AXES = [
    "history_taking",
    "assessment_accuracy",
    "differential_diagnosis",
    "evidence_based",
    "protocol_adherence",
    "treatment_safety",
    "personalization",
    "clarity",
    "pedagogical_value",
    "source_citation",
    "argentine_context",
]


def parse_benchmark(filepath: Path) -> list[dict]:
    """Parse the benchmark markdown file into structured Q&A pairs."""
    if not filepath.exists():
        print(f"❌ Benchmark file not found: {filepath}")
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")
    questions = []
    current = {}

    for line in content.split("\n"):
        line = line.strip()

        if line.startswith("### Pregunta #"):
            if current and "pregunta" in current:
                questions.append(current)
            current = {"id": line.replace("### Pregunta #", "").strip()}
        elif line.startswith("**Área**:"):
            current["area"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Tema**:"):
            current["tema"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Dificultad**:"):
            current["dificultad"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Modo**:"):
            current["modo"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("**Pregunta**:"):
            current["pregunta"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Respuesta esperada**:"):
            current["respuesta_esperada"] = ""
        elif line.startswith("**Fuentes de referencia**:"):
            current["fuentes"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Ejes OSCE**:"):
            current["ejes"] = [e.strip() for e in line.split(":", 1)[1].split(",")]
        elif "respuesta_esperada" in current and not line.startswith("**"):
            # Append to respuesta_esperada
            current["respuesta_esperada"] += line + "\n"

    if current and "pregunta" in current:
        questions.append(current)

    return questions


async def query_kineia(api_url: str, question: dict) -> dict:
    """Send a question to the KineIA API and return the response."""
    payload = {
        "query": question["pregunta"],
        "mode": question.get("modo", "student"),
        "area": question.get("area"),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "answer": data.get("data", {}).get("answer", ""),
            "sources": data.get("data", {}).get("sources", []),
            "response_time_ms": data.get("data", {}).get("response_time_ms", 0),
        }


def score_question(question: dict, kineia_response: dict) -> dict:
    """Score a single question across OSCE axes.

    This is a heuristic scoring function. For production use, axes should be
    scored by human experts (kinesiologists) using the double-blind protocol.
    """
    scores = {}
    answer = kineia_response.get("answer", "").lower()
    sources = kineia_response.get("sources", [])

    # Basic heuristics for automated pre-scoring
    scores["clarity"] = min(5, max(1, len(answer) // 100))  # rough proxy
    scores["source_citation"] = min(5, len(sources))  # more sources = better
    scores["pedagogical_value"] = 3  # default, needs human evaluation

    if question.get("area"):
        scores["argentine_context"] = 4  # area-specific implies Argentine focus

    # Response time scoring
    rt = kineia_response.get("response_time_ms", 0)
    if rt < 2000:
        scores["response_time"] = 5
    elif rt < 5000:
        scores["response_time"] = 4
    elif rt < 10000:
        scores["response_time"] = 3
    else:
        scores["response_time"] = 2

    return scores


async def run_evaluation(
    api_url: str,
    area_filter: str | None = None,
    mode_filter: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Run the full evaluation pipeline."""
    benchmark_file = BENCHMARK_DIR / "benchmark-preguntas.md"
    questions = parse_benchmark(benchmark_file)

    # Apply filters
    if area_filter:
        questions = [q for q in questions if q.get("area", "").lower() == area_filter.lower()]
    if mode_filter:
        questions = [q for q in questions if q.get("modo", "").lower() == mode_filter.lower()]
    if limit:
        questions = questions[:limit]

    print(f"🧠 KineIA OSCE Evaluation")
    print(f"   API: {api_url}")
    print(f"   Questions: {len(questions)}")
    print(f"   Filters: area={area_filter or 'all'}, mode={mode_filter or 'all'}")
    print(f"{'='*60}")

    results = []
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] {q.get('area', '?')} — {q.get('tema', '?')}")
        print(f"  Q: {q.get('pregunta', '?')[:100]}...")

        try:
            response = await query_kineia(api_url, q)
            scores = score_question(q, response)

            result = {
                "id": q.get("id", str(i)),
                "area": q.get("area", ""),
                "tema": q.get("tema", ""),
                "dificultad": q.get("dificultad", ""),
                "modo": q.get("modo", ""),
                "pregunta": q.get("pregunta", ""),
                "respuesta_kineia": response["answer"][:500],
                "fuentes_count": len(response.get("sources", [])),
                "response_time_ms": response.get("response_time_ms", 0),
                **scores,
            }
            results.append(result)
            total = sum(scores.values())
            max_score = len(scores) * 5
            print(f"  ✓ Score: {total}/{max_score} ({total*100//max_score}%) — {response.get('response_time_ms', 0)}ms")

        except httpx.ConnectError:
            print(f"  ❌ Connection failed — is KineIA running?")
            results.append({"id": q.get("id", str(i)), "error": "connection_failed"})
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({"id": q.get("id", str(i)), "error": str(e)})

    return results


def save_results(results: list[dict], output_dir: Path):
    """Save evaluation results to CSV and JSON."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    # CSV
    csv_path = output_dir / f"evaluation_{timestamp}.csv"
    if results:
        fieldnames = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n📊 CSV saved: {csv_path}")

    # JSON
    json_path = output_dir / f"evaluation_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"📊 JSON saved: {json_path}")

    # Summary
    valid = [r for r in results if "error" not in r]
    if valid:
        avg_time = sum(r.get("response_time_ms", 0) for r in valid) / len(valid)
        print(f"\n📈 Summary:")
        print(f"   Total questions: {len(results)}")
        print(f"   Successful: {len(valid)}")
        print(f"   Failed: {len(results) - len(valid)}")
        print(f"   Avg response time: {avg_time:.0f}ms")


async def main():
    parser = argparse.ArgumentParser(description="KineIA OSCE Evaluation")
    parser.add_argument("--api", default=DEFAULT_API, help="KineIA API URL")
    parser.add_argument("--area", help="Filter by area (traumatologia, neurologia, etc.)")
    parser.add_argument("--mode", help="Filter by mode (student, professional, exam)")
    parser.add_argument("--limit", type=int, help="Limit number of questions")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    results = await run_evaluation(
        api_url=args.api,
        area_filter=args.area,
        mode_filter=args.mode,
        limit=args.limit,
    )

    save_results(results, Path(args.output))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
