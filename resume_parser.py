import sys
from pathlib import Path
import pymupdf


def extract_resume_text(pdf_path):
    """Extracts clean plain text from a given PDF resume path using PyMuPDF."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    text_parts = []
    with pymupdf.open(pdf_path) as document:
        for page in document:
            # Sort text in logical reading order
            page_text = page.get_text("text", sort=True)
            if not page_text or len(page_text.strip()) < 15:
                blocks = page.get_text("blocks")
                page_text = "\n".join(b[4] for b in blocks if len(b) > 4 and str(b[4]).strip())
            if page_text.strip():
                text_parts.append(page_text)

    raw_text = "\n".join(text_parts)
    raw_text = raw_text.replace("\xa0", " ").replace("\x00", " ")
    return raw_text.strip()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_path = sys.argv[1].strip().strip('"')
    elif sys.stdin.isatty():
        target_path = input("Enter your PDF resume path: ").strip().strip('"')
    else:
        target_path = "sample_resume.pdf"

    if Path(target_path).exists():
        text = extract_resume_text(target_path)
        print(f"\nExtracted {len(text)} characters from {target_path}:\n")
        print(text[:300] + "...")
    else:
        print(f"Usage: python resume_parser.py <path_to_resume.pdf>")
