import json

import pytest

from app.services.classification.classifier import IncidentClassifier
from app.services.incident.extractor import IncidentExtractor, follow_up_questions
from app.services.incident.identifiers import extract_identifiers
from tests.conftest import DEMO

SCENARIOS = [
    ("phishing", DEMO),
    ("upi_fraud", "A buyer on OLX sent me a QR code and asked me to enter my UPI PIN to receive payment. "
                  "Rs 12,000 got debited to buyer99@ybl from my PhonePe yesterday."),
    ("banking_fraud", "I noticed an unauthorised transaction on my credit card statement today; Rs 45,000 was "
                      "debited from my bank account though I never made it."),
    ("social_media_impersonation", "Someone created a fake profile on Instagram using my name and photo and is "
                                   "asking my friends for money, pretending to be me."),
    ("job_scam", "I got a work from home part-time job offer on Telegram. The recruiter asked me to pay a "
                 "registration fee of Rs 2,500 before sending the offer letter."),
]


@pytest.mark.parametrize("expected,text", SCENARIOS)
def test_scenarios_classified(llm, expected, text):
    data, _ = IncidentExtractor(llm).extract(text)
    result = IncidentClassifier(llm).classify(data)
    assert result.category == expected
    assert 0 <= result.confidence <= 1
    assert result.reasoning


def test_ambiguous_incident_is_unknown(llm):
    data, _ = IncidentExtractor(llm).extract("Something weird happened online.")
    assert IncidentClassifier(llm).classify(data).category == "unknown"


def test_low_confidence_label_becomes_unknown(llm):
    from app.schemas.incident import IncidentData

    llm.queue["classification"].append(json.dumps({"category": "romance_scam", "confidence": 0.2, "reasoning": "weak"}))
    r = IncidentClassifier(llm).classify(IncidentData(description="x"))
    assert r.category == "unknown"
    assert r.alternatives[0].category == "romance_scam"


def test_demo_missing_information_and_questions(llm):
    data, _ = IncidentExtractor(llm).extract(DEMO)
    assert data.platform == "WhatsApp"
    assert data.field_sources["platform"].value == "inferred"
    assert data.date_time is None and data.amount is None  # never invented
    assert {"date_time", "financial_loss", "evidence"} <= set(data.missing_information)
    qs = follow_up_questions(data.missing_information)
    assert 1 <= len(qs) <= 3


def test_hallucinated_identifiers_are_dropped(llm):
    fake = {"description": "x", "phone_numbers": ["9999999999"], "urls": ["evil.example.com"], "amount": 50000,
            "upi_ids": [], "confidence": 0.9}
    llm.queue["extraction"].append(json.dumps(fake))
    data, _ = IncidentExtractor(llm).extract("I got a scam call from 9123456780 asking for my OTP.")
    assert data.phone_numbers == ["9123456780"]
    assert data.urls == []
    assert data.amount is None


def test_follow_up_details_merge_without_losing_facts(llm):
    ex = IncidentExtractor(llm)
    first, _ = ex.extract(DEMO)
    second, _ = ex.extract("It happened yesterday evening. I lost Rs 20,000, transaction id 312345678901.", first)
    assert second.platform == "WhatsApp"
    assert second.date_time and second.amount == 20000
    assert "date_time" not in second.missing_information
    assert "312345678901" in second.account_identifiers


def test_identifier_regexes():
    ids = extract_identifiers("Mail a.b@gmail.com, visit http://sbi-kyc.xyz/login, pay ram@okaxis, call +91 98765 43210, Rs 1.5 lakh")
    assert ids.emails == ["a.b@gmail.com"]
    assert ids.upi_ids == ["ram@okaxis"]
    assert ids.urls == ["http://sbi-kyc.xyz/login"]
    assert ids.phone_numbers and ids.amount == 150000
