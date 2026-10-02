from app.core.logging import redact


def test_redacts_secrets_and_identifiers():
    out = redact("api_key=sk-abcdefghijklmnop user a.b@gmail.com upi x@ybl phone 9876543210 Bearer abc.def")
    for secret in ("sk-abcdefghijklmnop", "a.b@gmail.com", "x@ybl", "9876543210", "abc.def"):
        assert secret not in out
