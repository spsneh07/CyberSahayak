import json

from app.services.scamcheck.red_flags import detect_red_flags, llm_explain

BANK_SMS = ("Dear Customer, your SBI account will be blocked within 24 hours. Update your KYC immediately at "
            "http://sbi-kyc-update.xyz/login and share the OTP sent to you.")


def test_spans_are_exact_substrings():
    r = detect_red_flags(BANK_SMS)
    assert r.spans
    for s in r.spans:
        assert BANK_SMS[s.start:s.end] == s.text
        assert s.explanation and s.label and s.explanation_source == "rule"


def test_bank_sms_categories():
    r = detect_red_flags(BANK_SMS)
    assert {"impersonation", "urgency_threat", "personal_info_request", "suspicious_link", "credential_request"} <= r.categories.keys()
    assert r.risk_level == "high"
    link = next(s for s in r.spans if s.category == "suspicious_link")
    assert link.text == "http://sbi-kyc-update.xyz/login"
    assert r.url_checks and r.url_checks[0].risk_level == "high"


def test_lottery_and_remote_access():
    r = detect_red_flags("Congratulations! You have won a lottery of Rs 25,00,000. Pay processing fee of Rs 4,999 "
                         "to claim. Install AnyDesk so our executive can help.")
    assert {"too_good_to_be_true", "payment_request", "remote_access"} <= r.categories.keys()


def test_hindi_message():
    r = detect_red_flags("आपका खाता बंद हो जाएगा। तुरंत ओटीपी बताएं।")
    assert {"urgency_threat", "credential_request"} <= r.categories.keys()


def test_benign_message_has_no_flags():
    r = detect_red_flags("Hi Ma, I will reach home by 7. Can you keep dinner ready?")
    assert r.spans == [] and r.risk_level == "none_found"
    assert "does not mean the message is safe" in r.summary


def test_official_link_alone_is_low():
    r = detect_red_flags("Your order has shipped. Track it at https://www.amazon.in/orders")
    assert r.risk_level == "low" and r.categories == {"suspicious_link": 1}


def test_email_is_not_a_link():
    r = detect_red_flags("Write to support@example.com for help.")
    assert "suspicious_link" not in r.categories


class _FakeLLM:
    name = "fake"

    def __init__(self, payload: dict):
        self.payload, self.system = payload, ""

    def complete(self, *, task, system, user, json_schema=None):
        self.system = system
        return json.dumps(self.payload)


def test_llm_may_only_reword_existing_spans():
    r = detect_red_flags(BANK_SMS)
    before = [(s.start, s.end, s.text, s.category) for s in r.spans]
    llm = _FakeLLM({"explanations": [
        {"index": 0, "explanation": "Real banks address you by name."},
        {"index": 1, "explanation": "Call 1800123456 now."},          # adds a number: rejected
        {"index": 2, "explanation": "Visit https://evil.example."},   # adds a link: rejected
        {"index": 3, "explanation": "Delete the message right away."},  # destroys evidence: rejected
        {"index": 99, "explanation": "Invented flag."},               # no such span: ignored
    ]})
    out = llm_explain(r, llm)
    assert [(s.start, s.end, s.text, s.category) for s in out.spans] == before
    assert out.spans[0].explanation_source == "llm"
    assert all(s.explanation_source == "rule" for s in out.spans[1:])


def test_llm_failure_keeps_rules():
    r = detect_red_flags(BANK_SMS)
    out = llm_explain(r, _FakeLLM({"unexpected": True}))
    assert all(s.explanation_source == "rule" for s in out.spans)
