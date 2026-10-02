"""Regression tests for complaint hallucination (unsupported factual claims in the narrative)."""
import json

import pytest

from app.schemas.classification import ClassificationResult
from app.schemas.incident import IncidentData
from app.services.complaint.generator import ComplaintGenerator
from app.services.complaint.validator import validate_narrative

DEMO = ("I received a WhatsApp message claiming to be from my bank. It asked me to click a link and enter my OTP "
        "because my account would otherwise be blocked.")
CLS = ClassificationResult(category="phishing", confidence=0.9, reasoning="r")


def demo_incident(**kw) -> IncidentData:
    return IncidentData(description=DEMO, platform="WhatsApp", **kw)


# Exact sentences produced by real models during validation (gpt-oss-120b / gpt-oss-20b, 2026-10-02).
@pytest.mark.parametrize("claim", [
    "No financial loss has occurred, and I have not taken any further action.",
    "I have not yet taken any action to report the incident.",
    "I have not taken any further action.",
])
def test_observed_no_action_claims_are_removed(claim):
    text, notes = validate_narrative(f"{DEMO} {claim}", demo_incident())
    assert "action" not in text.lower()
    assert notes


@pytest.mark.parametrize("claim", [
    "I immediately informed my bank and blocked my card.",
    "I have already reported this to the police.",
    "No further steps were taken.",
])
def test_action_claims_without_recorded_actions_are_removed(claim):
    text, _ = validate_narrative(f"{DEMO} {claim}", demo_incident())
    assert claim not in text


def test_action_claim_supported_by_recorded_actions_is_kept():
    incident = demo_incident(actions_taken=["Informed the bank by phone and blocked the card"])
    text, notes = validate_narrative("I informed my bank and blocked the card.", incident)
    assert "blocked the card" in text and not notes


def test_no_loss_claim_requires_financial_loss_false():
    claim = "No financial loss has occurred."
    assert claim not in validate_narrative(claim, demo_incident())[0]                       # unknown
    assert claim in validate_narrative(claim, demo_incident(financial_loss=False))[0]       # stated


def test_loss_claim_requires_recorded_loss():
    text, _ = validate_narrative("Rs 5,000 was debited from my account.", demo_incident())
    assert "debited" not in text
    text, _ = validate_narrative("Rs 5,000 was debited from my account.",
                                 demo_incident(financial_loss=True, amount=5000, currency="INR"))
    assert "Rs 5,000" in text


def test_wrong_amount_is_replaced():
    text, notes = validate_narrative("I lost Rs 50,000.", demo_incident(financial_loss=True, amount=5000))
    assert "50,000" not in text and "[AMOUNT]" in text and notes


def test_invented_date_and_time_are_replaced_but_stated_ones_kept():
    text, _ = validate_narrative("On 12 March 2026 at 9 pm I received the message.", demo_incident())
    assert "[DATE]" in text and "[TIME]" in text
    text, _ = validate_narrative("At 7 pm yesterday I received the message.",
                                 demo_incident(date_time="yesterday evening around 7 pm"))
    assert "7 pm" in text


def test_disclosure_claims_must_match_user_statement():
    # The user never said whether they shared anything: both polarities are unsupported.
    for claim in ("I did not share the OTP with anyone.", "I shared the OTP with the caller."):
        assert claim not in validate_narrative(claim, demo_incident())[0]
    # Stated by the user (same polarity) -> kept.
    incident = IncidentData(description=DEMO + " I did not share the OTP.", platform="WhatsApp")
    assert "did not share" in validate_narrative("I did not share the OTP.", incident)[0]


def test_user_facts_survive_validation():
    text, notes = validate_narrative(DEMO, demo_incident())
    assert text == DEMO and notes == []


def test_generator_applies_validation_and_reports_notes(llm):
    llm.queue["complaint"].append(json.dumps({
        "narrative": DEMO + " I have not yet taken any action to report the incident.",
        "requested_assistance": ["Investigate"]}))
    _, body, placeholders, notes = ComplaintGenerator(llm).generate(demo_incident(), CLS)
    assert "not yet taken any action" not in body
    assert notes and "[ACTIONS ALREADY TAKEN, E.G. BANK INFORMED ON DATE, REFERENCE NO.]" in placeholders
