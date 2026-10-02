import pytest

from app.services.scamcheck.url_analyzer import analyze_url


def codes(url: str) -> set[str]:
    return {i.code for i in analyze_url(url).indicators}


@pytest.mark.parametrize("url", [
    "https://www.hdfcbank.com/personal",
    "https://onlinesbi.sbi/",
    "https://www.irctc.co.in/nget/train-search",
    "https://www.google.com/search?q=weather",
])
def test_official_domains_are_low_risk(url):
    r = analyze_url(url)
    assert r.risk_level == "low"
    assert not [i for i in r.indicators if i.severity != "info"]


@pytest.mark.parametrize("url", [
    "https://www.my-local-bakery.in",
    "https://example.org/about",
    "https://taxisinfo.com",  # contains "axis" inside another word: not a brand claim
    "https://shop.unfamiliar-store.com/products/42",
])
def test_unfamiliar_domains_are_not_flagged(url):
    r = analyze_url(url)
    assert r.risk_level == "low" and r.score == 0, r.indicators
    assert "not a verdict" in r.explanation


def test_brand_in_subdomain():
    r = analyze_url("https://hdfcbank.com.secure-login.top/verify")
    assert r.registered_domain == "secure-login.top"
    assert {"brand_in_subdomain", "unusual_tld", "sensitive_path_words"} <= codes(r.input)
    assert r.risk_level == "high"


def test_character_substitution_and_typosquat():
    assert "character_substitution" in codes("http://paytrn.com")
    assert "character_substitution" in codes("https://fl1pkart.com")
    assert "typosquat" in codes("https://flipkarrt.com")


def test_punycode_brand_imitation():
    r = analyze_url("https://xn--pple-43d.com")  # Cyrillic "а" + "pple"
    assert "punycode" in codes(r.input) and r.risk_level == "high"
    assert analyze_url("https://аpple.com").registered_domain == "xn--pple-43d.com"


def test_embedded_credentials_ip_and_apk():
    c = codes("http://www.sbi.co.in@192.168.1.4/app.apk")
    assert {"embedded_credentials", "ip_address_host", "executable_download", "no_https"} <= c


def test_fake_government_and_redirect():
    c = codes("https://incometax-gov.in.refund-claim.online/?next=https://evil.example")
    assert {"fake_government", "redirect_parameter"} <= c
    assert "fake_government" not in codes("https://www.incometax.gov.in/iec/foportal/")


def test_encoding_hyphens_shortener_tld():
    assert "heavy_encoding" in codes("https://a.com/%2568%2574%2574%2570")
    assert "many_hyphens" in codes("https://secure-bank-login-verify-now.com")
    assert "url_shortener" in codes("https://bit.ly/3abc")
    assert "unusual_tld" in codes("https://prize-claim.xyz")


def test_normalization_and_invalid():
    r = analyze_url("  WWW.Example.COM/Path ")
    assert r.normalized_url == "http://www.example.com/Path" and r.domain == "www.example.com"
    assert "no_scheme" in codes("example.com")
    assert analyze_url("not a url").risk_level == "invalid"


def test_no_network_access(monkeypatch):
    import socket

    def boom(*a, **k):
        raise AssertionError("URL analysis must not touch the network")

    monkeypatch.setattr(socket, "getaddrinfo", boom)
    monkeypatch.setattr(socket.socket, "connect", boom)
    analyze_url("https://hdfcbank.com.secure-login.top/verify")
