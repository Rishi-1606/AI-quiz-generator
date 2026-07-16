"""
Text Processor Service
-----------------------
Cleans raw extracted text and splits it into smaller chunks
so Gemini AI can process it without hitting token limits.

Two main functions:
  - clean_text(text)  → removes noise from raw extracted text
  - chunk_text(text)  → splits clean text into overlapping chunks
"""

import re


# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

# Maximum number of words per chunk sent to the AI
CHUNK_SIZE_WORDS = 800

# Overlap between consecutive chunks (so context isn't lost at boundaries)
CHUNK_OVERLAP_WORDS = 80


# ─────────────────────────────────────────
# CLEANING
# ─────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Remove common noise from raw extracted text.

    Steps:
    1. Normalize unicode dashes/quotes to ASCII equivalents.
    2. Remove standalone page numbers (e.g. "Page 3", "- 12 -", lone digits on a line).
    3. Strip lines that are purely non-alphanumeric (decorative lines, borders).
    4. Collapse 3+ consecutive blank lines into a single blank line.
    5. Strip leading/trailing whitespace from each line.
    6. Strip overall leading/trailing whitespace.
    """
    if not text:
        return ""

    # 1. Normalize unicode punctuation
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00a0", " ")  # non-breaking space

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # 2. Remove standalone page numbers
        if re.fullmatch(r"(page\s*)?\d{1,4}", stripped, re.IGNORECASE):
            continue
        if re.fullmatch(r"[-–—]\s*\d{1,4}\s*[-–—]", stripped):
            continue

        # 3. Remove decorative/separator lines (only symbols, no letters/digits)
        if stripped and not re.search(r"[a-zA-Z0-9]", stripped):
            continue

        cleaned.append(stripped)

    # 4. Collapse 3+ consecutive blank lines → single blank line
    result_lines = []
    blank_run = 0
    for line in cleaned:
        if line == "":
            blank_run += 1
            if blank_run <= 1:
                result_lines.append(line)
        else:
            blank_run = 0
            result_lines.append(line)

    return "\n".join(result_lines).strip()


# ─────────────────────────────────────────
# CHUNKING
# ─────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    Why overlapping?
    If a concept spans two chunks, the overlap ensures the AI sees
    the end of the previous chunk at the start of the next one,
    so no context is lost at boundaries.

    Args:
        text      : Cleaned text to chunk.
        chunk_size: Max words per chunk (default 800).
        overlap   : Words shared between consecutive chunks (default 80).

    Returns:
        List of text chunk strings.
    """
    if not text:
        return []

    words = text.split()

    if len(words) <= chunk_size:
        # Text is short enough — return as a single chunk
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        # Move forward by (chunk_size - overlap) to create the overlap
        start += chunk_size - overlap

    return chunks


# ─────────────────────────────────────────
# COMBINED PIPELINE
# ─────────────────────────────────────────

def process_text(raw_text: str) -> dict:
    """
    Full pipeline: clean → chunk.

    Returns a dict with:
      - "cleaned_text"  : the cleaned full text
      - "chunks"        : list of chunk strings
      - "word_count"    : total word count of cleaned text
      - "chunk_count"   : number of chunks produced
    """
    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned)

    return {
        "cleaned_text": cleaned,
        "chunks": chunks,
        "word_count": len(cleaned.split()) if cleaned else 0,
        "chunk_count": len(chunks),
    }
