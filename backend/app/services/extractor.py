import re


def extract_text_from_txt(file_path: str) -> str:
    """
    Read a plain text file and return cleaned text.

    Cleaning steps:
    - Decode with UTF-8 (fallback to latin-1 if needed)
    - Normalize line endings (Windows CRLF → LF)
    - Collapse more than 2 consecutive blank lines into one blank line
    - Strip leading/trailing whitespace from each line
    - Strip overall leading/trailing whitespace from the result
    """
    # Read raw content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except UnicodeDecodeError:
        # Fallback for files saved with Windows Latin-1 encoding
        with open(file_path, "r", encoding="latin-1") as f:
            raw_text = f.read()

    # Normalize line endings
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse more than 2 consecutive blank lines into a single blank line
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if line == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    # Re-join and strip overall whitespace
    cleaned_text = "\n".join(cleaned_lines).strip()

    return cleaned_text


def extract_text(file_path: str, file_type: str) -> str:
    """
    Route to the correct extractor based on file type.
    Returns extracted and cleaned text, or empty string if unsupported.
    """
    if file_type == "txt":
        return extract_text_from_txt(file_path)

    # PDF, DOCX, PPTX extractors will be added in later steps
    return ""
