"""Offline lookalike-URL analysis.

Rule-based and static: it inspects only the text of the URL. It never opens, resolves
or fetches the URL. An unfamiliar domain is NOT treated as an indicator on its own;
only specific, explainable structural patterns are reported.
"""
import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urlsplit

from pydantic import BaseModel, Field

# Brand keyword -> registered domains that officially belong to it.
BRANDS: dict[str, tuple[str, ...]] = {
    "sbi": ("sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "sbicard.com"),
    "hdfc": ("hdfcbank.com", "hdfc.com", "hdfcbank.bank.in"),
    "icici": ("icicibank.com", "icici.bank.in"),
    "axis": ("axisbank.com", "axis.bank.in"),
    "kotak": ("kotak.com", "kotak.bank.in"),
    "paytm": ("paytm.com", "paytmbank.com"),
    "phonepe": ("phonepe.com",),
    "gpay": ("google.com",),
    "google": ("google.com", "google.co.in"),
    "amazon": ("amazon.in", "amazon.com"),
    "flipkart": ("flipkart.com",),
    "npci": ("npci.org.in",),
    "rbi": ("rbi.org.in",),
    "uidai": ("uidai.gov.in",),
    "aadhaar": ("uidai.gov.in",),
    "incometax": ("incometax.gov.in",),
    "irctc": ("irctc.co.in",),
    "indiapost": ("indiapost.gov.in",),
    "whatsapp": ("whatsapp.com",),
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
    "microsoft": ("microsoft.com",),
    "apple": ("apple.com",),
    "netflix": ("netflix.com",),
    "paypal": ("paypal.com",),
}
# Brand keywords up to this length must start a token (e.g. "axis" must not match "taxis");
# shorter ones must be a whole token; longer ones may appear anywhere in the host.
_SHORT_BRAND = 4

TWO_LEVEL_SUFFIXES = {
    "co.in", "gov.in", "nic.in", "org.in", "net.in", "ac.in", "edu.in", "res.in", "firm.in", "gen.in", "ind.in",
    "bank.in", "co.uk", "org.uk", "gov.uk", "ac.uk", "com.au", "co.jp",
}
UNUSUAL_TLDS = {
    "xyz", "top", "tk", "ml", "ga", "cf", "gq", "click", "link", "buzz", "rest", "icu", "cyou", "sbs", "loan",
    "work", "zip", "mov", "country", "kim", "fit", "monster", "bar", "cam", "quest", "support", "live",
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy", "ow.ly", "shorturl.at", "tiny.cc"}
PATH_WORDS = re.compile(
    r"(login|log-in|signin|sign-in|verify|verification|kyc|update|secure|account|otp|password|passwd|reward|"
    r"refund|cashback|wallet|unlock|suspend|blocked|confirm|claim|prize|lottery)", re.I)
RISKY_FILE = re.compile(r"\.(apk|exe|scr|bat|msi|jar|vbs)(?:$|[?#])", re.I)
REDIRECT_KEYS = {"url", "redirect", "redirect_url", "next", "return", "returnurl", "goto", "dest", "destination", "continue"}
# Look-alike substitutions undone before comparing a label with brand names.
SUBSTITUTIONS = [("rn", "m"), ("vv", "w"), ("0", "o"), ("1", "l"), ("3", "e"), ("4", "a"), ("5", "s"), ("7", "t"),
                 ("8", "b"), ("@", "a"), ("$", "s")]


# Common non-Latin letters that look like Latin ones (Cyrillic/Greek), used to build a comparison skeleton.
CONFUSABLES = {"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ј": "j", "ѕ": "s",
               "ԁ": "d", "һ": "h", "ӏ": "l", "ο": "o", "α": "a", "ν": "v", "κ": "k", "τ": "t"}


class UrlIndicator(BaseModel):
    code: str
    severity: str = Field(description="info | low | medium | high")
    message: str


class UrlAnalysis(BaseModel):
    input: str
    normalized_url: str | None
    domain: str | None
    registered_domain: str | None
    indicators: list[UrlIndicator]
    risk_level: str = Field(description="low | medium | high | invalid")
    score: int
    explanation: str
    method: str = "rule-based static analysis (no request made to the URL)"


_WEIGHT = {"info": 0, "low": 1, "medium": 2, "high": 4}


@dataclass
class _Parts:
    scheme: str
    scheme_given: bool
    host: str
    userinfo: str
    path: str
    query: str


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _desubstitute(label: str) -> str:
    out = label
    for src, dst in SUBSTITUTIONS:
        out = out.replace(src, dst)
    return out


def _readings(label: str) -> set[str]:
    """Plausible readings of a label with look-alike characters undone ("1" may stand for "l" or "i")."""
    return {_desubstitute(label), _desubstitute(label.replace("1", "i"))}


def registered_domain(host: str) -> str:
    labels = host.split(".")
    if len(labels) >= 3 and ".".join(labels[-2:]) in TWO_LEVEL_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def _split(raw: str) -> _Parts | None:
    text = raw.strip().strip("<>\"'")
    scheme_given = bool(re.match(r"^[a-z][a-z0-9+.-]*://", text, re.I))
    if not scheme_given:
        text = "http://" + text
    try:
        parts = urlsplit(text)
        host = parts.hostname or ""
    except ValueError:
        return None
    if not host or re.search(r"\s", host) or ("." not in host and ":" not in host):
        return None
    netloc = parts.netloc
    userinfo = netloc.rsplit("@", 1)[0] if "@" in netloc else ""
    return _Parts(parts.scheme.lower(), scheme_given, host.lower().rstrip("."), userinfo, parts.path, parts.query)


def _decode_host(host: str) -> tuple[str, str | None]:
    """Return (ascii_host, unicode_host_or_None)."""
    try:
        if any(ord(c) > 127 for c in host):
            ascii_host = host.encode("idna").decode("ascii")
            return ascii_host, host
        if "xn--" in host:
            return host, host.encode("ascii").decode("idna")
    except UnicodeError:
        pass
    return host, None


def _brand_hits(host: str) -> set[str]:
    tokens = set(re.split(r"[.\-_]", host))
    joined = host.replace("-", "").replace(".", "")
    hits = set()
    for brand, officials in BRANDS.items():
        keys = {brand} | {o.split(".")[0] for o in officials}
        if any(k in tokens or (len(k) > _SHORT_BRAND and k in joined)
               or (len(k) == _SHORT_BRAND and any(t.startswith(k) for t in tokens)) for k in keys):
            hits.add(brand)
    return hits


def _is_official(reg: str, brand: str) -> bool:
    return reg in BRANDS[brand]


def analyze_url(raw: str) -> UrlAnalysis:
    ind: list[UrlIndicator] = []

    def add(code: str, severity: str, message: str) -> None:
        if not any(i.code == code for i in ind):
            ind.append(UrlIndicator(code=code, severity=severity, message=message))

    parts = _split(raw)
    if parts is None:
        return UrlAnalysis(input=raw, normalized_url=None, domain=None, registered_domain=None, indicators=[],
                           risk_level="invalid", score=0, explanation="This does not look like a web address that can be analysed.")

    ascii_host, unicode_host = _decode_host(parts.host)
    host = ascii_host

    if parts.scheme not in ("http", "https"):
        add("non_web_scheme", "medium", f"Uses the '{parts.scheme}' scheme rather than a normal web address (http/https).")
    if not parts.scheme_given:
        add("no_scheme", "info", "No http:// or https:// was given; the address was read as a web address for analysis only.")
    elif parts.scheme == "http":
        add("no_https", "low", "Uses plain HTTP, so data sent to it is not encrypted. (HTTPS on its own does not prove a site is genuine.)")

    if parts.userinfo:
        add("embedded_credentials", "high",
            "Contains text before an '@' in the address. Browsers ignore that part, so a URL like "
            "'https://bank.com@other.site' actually opens 'other.site'.")

    if unicode_host:
        skeleton = "".join(CONFUSABLES.get(c, c) for c in unicode_host)
        mimics = _brand_hits(skeleton)  # a non-Latin spelling of a known brand
        add("punycode", "high" if mimics else "medium",
            f"Uses internationalised characters (punycode). It displays as '{unicode_host}' but is really '{ascii_host}'; "
            "non-Latin letters can imitate familiar names.")

    is_ip = False
    try:
        ipaddress.ip_address(host.strip("[]"))
        is_ip = True
        add("ip_address_host", "medium", "Uses a raw IP address instead of a domain name; genuine banks and services use named domains.")
    except ValueError:
        pass

    if "%" in parts.host:
        add("encoded_host", "high", "The domain part contains percent-encoding, which is used to disguise the real host.")

    reg = host if is_ip else registered_domain(host)
    labels = host.split(".")
    reg_label = reg.split(".")[0]
    tld = labels[-1] if not is_ip else ""
    subdomains = [] if is_ip else labels[: len(labels) - len(reg.split("."))]

    if not is_ip:
        if tld in UNUSUAL_TLDS:
            add("unusual_tld", "low", f"Uses the '.{tld}' ending, which is cheap to register and often seen in scam links. Many legitimate sites use it too.")
        if reg in SHORTENERS:
            add("url_shortener", "low", "This is a link shortener, so the real destination is hidden until opened. Expand it with a preview service rather than clicking.")
        plain = host.replace("xn--", "")
        if reg_label.replace("xn--", "").count("-") >= 3 or plain.count("-") >= 4:
            add("many_hyphens", "medium", "The domain has many hyphens, a pattern often used to string together trusted-sounding words.")
        if len(subdomains) >= 3:
            add("deep_subdomains", "medium", f"Has {len(subdomains)} levels of subdomain; long chains can push the real domain ('{reg}') out of view on small screens.")
        if re.search(r"\b(gov|nic)\b", ".".join(subdomains + [reg_label]).replace("-", ".")) and not (host.endswith(".gov.in") or host.endswith(".nic.in")):
            add("fake_government", "high", "Mentions 'gov' or 'nic' but is not under .gov.in or .nic.in, where Indian government sites live.")

        # Brand misuse: brand appears in the host, but the registered domain is not that brand's.
        hits = _brand_hits(host)
        for brand in sorted(hits):
            if _is_official(reg, brand):
                add("official_domain", "info", f"The registered domain '{reg}' is listed as an official domain of '{brand}' in this tool's small reference list.")
            elif _brand_hits(".".join(subdomains)) & {brand}:
                add("brand_in_subdomain", "high", f"'{brand}' appears in the subdomain, but the actual registered domain is '{reg}', which is not an official {brand} domain.")
            else:
                add("misleading_brand", "medium", f"The domain contains '{brand}' but '{reg}' is not one of its official domains in this tool's reference list.")

        # Look-alike spelling of a brand's registered label.
        readings = _readings(reg_label.replace("-", ""))
        for brand, officials in BRANDS.items():
            if _is_official(reg, brand):
                continue
            official_labels = {o.split(".")[0] for o in officials}
            for target in official_labels | {brand}:
                if len(target) < 5 or reg_label == target:
                    continue
                if target in readings:
                    add("character_substitution", "high", f"'{reg_label}' imitates '{target}' by swapping look-alike characters (for example 0 for o, 1 for l, rn for m).")
                elif _levenshtein(reg_label, target) == 1 and len(reg_label) >= 5:
                    add("typosquat", "high", f"'{reg_label}' differs from '{target}' by a single character.")

    path_query = unquote(parts.path + "?" + parts.query)
    if re.search(r"%[0-9a-f]{2}", parts.path + parts.query, re.I):
        encoded = len(re.findall(r"%[0-9a-f]{2}", parts.path + parts.query, re.I))
        if "%25" in (parts.path + parts.query).lower() or encoded >= 6:
            add("heavy_encoding", "medium", "The path or query is heavily percent-encoded (or double-encoded), which can hide what the link really does.")
    words = sorted({w.lower() for w in PATH_WORDS.findall(path_query)})
    if words:
        add("sensitive_path_words", "low", f"The path or query contains words often used in phishing pages: {', '.join(words[:5])}.")
    if RISKY_FILE.search(parts.path):
        add("executable_download", "high", "Points directly to an app or program file (for example .apk/.exe). Installing apps from links is a common way to take over phones.")
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in REDIRECT_KEYS and re.match(r"(https?:)?//", unquote(value)):
            add("redirect_parameter", "medium", "Contains a redirect to another address in its query string; the final destination may differ from what is shown.")
    if "@" in parts.path:
        add("at_in_path", "low", "Contains '@' in the path, sometimes used to confuse readers about the destination.")
    if len(raw) > 120:
        add("very_long", "low", "The address is unusually long, which can hide the real domain.")

    score = sum(_WEIGHT[i.severity] for i in ind)
    level = "high" if score >= 4 else "medium" if score >= 2 else "low"
    normalized = f"{parts.scheme}://{host}{parts.path or '/'}" + (f"?{parts.query}" if parts.query else "")

    findings = [i for i in ind if i.severity != "info"]
    if not findings:
        explanation = ("No structural warning signs were found in this address. This is a static check of the URL text only, "
                       "not a verdict on the site: being unfamiliar is not a reason to call it malicious, but a clean result "
                       "does not prove it is safe either.")
    else:
        explanation = (f"Found {len(findings)} structural warning sign(s); overall risk from these signs is {level}. "
                       "This is a static check of the URL text only — no request was made to the site — so it describes "
                       "how the address is built, not what the site contains.")
    return UrlAnalysis(input=raw, normalized_url=normalized, domain=unicode_host or host, registered_domain=reg,
                       indicators=ind, risk_level=level, score=score, explanation=explanation)
