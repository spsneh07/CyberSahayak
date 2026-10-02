"""Heading-aware paragraph chunking with a one-paragraph overlap."""
import re


def chunk_text(text: str, max_chars: int = 900, title: str = "") -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    heading = title

    def flush() -> None:
        if current:
            body = "\n\n".join(current)
            chunks.append(f"{heading}\n\n{body}" if heading and not body.startswith("#") else body)

    for para in paragraphs:
        if para.startswith("#"):
            flush()
            current = []
            heading = para.lstrip("# ").strip()
            continue
        # Split oversized paragraphs on sentence boundaries.
        pieces = [para] if len(para) <= max_chars else _split_sentences(para, max_chars)
        for piece in pieces:
            if current and sum(len(c) for c in current) + len(piece) > max_chars:
                flush()
                current = current[-1:] if len(current[-1]) < max_chars // 3 else []
            current.append(piece)
    flush()
    return chunks


def _split_sentences(para: str, max_chars: int) -> list[str]:
    out, buf = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", para):
        if buf and len(buf) + len(sent) + 1 > max_chars:
            out.append(buf)
            buf = sent
        else:
            buf = f"{buf} {sent}".strip()
    if buf:
        out.append(buf)
    return out
