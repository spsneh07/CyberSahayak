"""Evaluate extraction + classification on the fictional dataset with the CONFIGURED provider.

Usage (from backend/):  python -m evaluation.run_eval [--out evaluation/results.json]

Metrics are computed fresh on every run and are only valid for the provider/model
recorded in the output. The dataset is small and fictional — results indicate
behaviour, not real-world accuracy.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.services.ai.factory import get_llm
from app.services.classification.classifier import IncidentClassifier
from app.services.incident.extractor import IncidentExtractor
from app.services.incident.identifiers import normalize

HERE = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(HERE / "dataset.jsonl"))
    parser.add_argument("--out", default=str(HERE / "results.json"))
    args = parser.parse_args()

    settings, llm = get_settings(), get_llm()
    extractor, classifier = IncidentExtractor(llm), IncidentClassifier(llm)
    cases = [json.loads(line) for line in Path(args.dataset).read_text(encoding="utf-8").splitlines() if line.strip()]

    rows, exact, lenient, id_checks, id_hits = [], 0, 0, 0, 0
    for case in cases:
        data, warnings = extractor.extract(case["text"])
        cls = classifier.classify(data)
        ok_exact = cls.category == case["expected_category"]
        ok_lenient = ok_exact or cls.category in case["acceptable"]
        exact += ok_exact
        lenient += ok_lenient
        for field, expected in case["expected_identifiers"].items():
            id_checks += 1
            got = getattr(data, field)
            hit = got == expected if field == "amount" else {normalize(v) for v in expected} <= {normalize(v) for v in got}
            id_hits += hit
        rows.append({"id": case["id"], "expected": case["expected_category"], "predicted": cls.category,
                     "confidence": cls.confidence, "correct": ok_exact, "acceptable": ok_lenient, "warnings": warnings})
        print(f"{case['id']}: expected={case['expected_category']:<28} predicted={cls.category:<28} {'OK' if ok_exact else ('~' if ok_lenient else 'X')}")

    n = len(cases)
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model if settings.llm_provider != "mock" else "mock-heuristic",
        "cases": n,
        "classification_exact_accuracy": round(exact / n, 3),
        "classification_lenient_accuracy": round(lenient / n, 3),
        "identifier_checks": id_checks,
        "identifier_accuracy": round(id_hits / id_checks, 3) if id_checks else None,
        "note": "Small fictional dataset; not a measure of real-world performance.",
    }
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
