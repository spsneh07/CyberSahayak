import pytest

from app.schemas.classification import ClassificationResult
from app.services.ai.base import StructuredOutputError
from app.services.ai.structured import generate_structured, parse_json_object
from app.services.classification.classifier import IncidentClassifier
from app.services.incident.extractor import IncidentExtractor

VALID = '{"category": "phishing", "confidence": 0.8, "reasoning": "link + OTP", "alternatives": []}'


def test_parse_tolerates_fences_and_prose():
    assert parse_json_object("```json\n{\"a\": 1}\n```") == {"a": 1}
    assert parse_json_object("Sure! Here it is: {\"a\": 2} hope that helps") == {"a": 2}


def test_parse_rejects_non_object():
    with pytest.raises(ValueError):
        parse_json_object("[1, 2]")


def test_repairs_after_one_malformed_reply(llm):
    llm.queue["classification"].extend(["not json at all", VALID])
    out = generate_structured(llm, task="classification", system="s", user="u", schema=ClassificationResult)
    assert out.category == "phishing"
    assert llm.calls == ["classification", "classification"]


def test_invalid_schema_twice_raises(llm):
    llm.queue["classification"].extend(['{"category": "made_up_type", "confidence": 2}'] * 2)
    with pytest.raises(StructuredOutputError):
        generate_structured(llm, task="classification", system="s", user="u", schema=ClassificationResult)


def test_classifier_falls_back_to_unknown_on_garbage(llm):
    from app.schemas.incident import IncidentData

    llm.queue["classification"].extend(["garbage", "{broken"])
    result = IncidentClassifier(llm).classify(IncidentData(description="something happened"))
    assert result.category == "unknown" and result.confidence == 0.0


def test_extractor_falls_back_to_regex_on_garbage(llm):
    llm.queue["extraction"].extend(["nope", "still nope"])
    data, warnings = IncidentExtractor(llm).extract("Fraudster 9876543210 took Rs 5,000 via pay.me@ybl")
    assert warnings
    assert data.phone_numbers == ["9876543210"]
    assert data.upi_ids == ["pay.me@ybl"]
    assert data.amount == 5000


def test_category_aliases_normalised():
    r = ClassificationResult.model_validate({"category": "UPI / payment fraud", "confidence": 0.7})
    assert r.category == "upi_fraud"
