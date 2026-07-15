import fitz  # PyMuPDF
import docx  # python-docx


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


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyMuPDF.

    - Opens each page and extracts plain text.
    - Pages are separated by a newline.
    - Collapses more than 2 consecutive blank lines into one.
    - Strips overall leading/trailing whitespace.
    """
    doc = fitz.open(file_path)
    pages_text = []

    for page in doc:
        page_text = page.get_text("text")  # Extract plain text from the page
        pages_text.append(page_text)

    doc.close()

    # Join all pages
    full_text = "\n".join(pages_text)

    # Normalize line endings
    full_text = full_text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in full_text.split("\n")]

    # Collapse more than 2 consecutive blank lines into one
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

    return "\n".join(cleaned_lines).strip()


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a .docx Word document using python-docx.

    - Reads every paragraph in the document in order.
    - Preserves paragraph breaks as newlines.
    - Collapses more than 2 consecutive blank lines into one.
    - Strips overall leading/trailing whitespace.
    """
    document = docx.Document(file_path)

    # Each paragraph becomes one line
    lines = [paragraph.text for paragraph in document.paragraphs]

    # Collapse more than 2 consecutive blank lines into one
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            blank_count += 1
            if blank_count <= 1:
                cleaned_lines.append(stripped)
        else:
            blank_count = 0
            cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()


def extract_text(file_path: str, file_type: str) -> str:
    """
    Route to the correct extractor based on file type.
    Returns extracted and cleaned text, or empty string if unsupported.
    """
    if file_type == "txt":
        return extract_text_from_txt(file_path)

    if file_type == "pdf":
        return extract_text_from_pdf(file_path)

    if file_type == "docx":
        return extract_text_from_docx(file_path)

    # PPTX extractor will be added in the next step
    return ""
