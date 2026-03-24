"""OCR support for scanned/image-based PDFs using Tesseract."""

import io
import logging

logger = logging.getLogger(__name__)


def is_scanned_pdf(file_bytes: bytes) -> bool:
    """Check if a PDF is scanned (image-based) by testing if pdfplumber extracts minimal text."""
    import pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            total_text = ""
            for page in pdf.pages[:3]:  # Check first 3 pages
                text = page.extract_text() or ""
                total_text += text
            # If very little text found relative to page count, likely scanned
            return len(total_text.strip()) < 50 * min(len(pdf.pages), 3)
    except Exception:
        return False


def ocr_pdf(file_bytes: bytes) -> str:
    """Extract text from a scanned PDF using Tesseract OCR via pdf2image + pytesseract."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as e:
        raise ImportError(
            f"OCR dependencies not installed: {e}. "
            "Install with: pip install pytesseract pdf2image Pillow\n"
            "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
        )

    try:
        images = convert_from_bytes(file_bytes, dpi=300)
    except Exception as e:
        raise RuntimeError(
            f"Failed to convert PDF to images: {e}. "
            "Ensure poppler is installed: https://poppler.freedesktop.org/"
        )

    text_parts = []
    for i, image in enumerate(images):
        try:
            text = pytesseract.image_to_string(image, lang="eng")
            if text.strip():
                text_parts.append(f"--- Page {i + 1} ---\n{text}")
        except Exception as e:
            logger.warning(f"OCR failed on page {i + 1}: {e}")
            text_parts.append(f"--- Page {i + 1} --- [OCR Error: {e}]")

    return "\n\n".join(text_parts)


def ocr_image(file_bytes: bytes) -> str:
    """Extract text from a standalone image file (PNG, JPG, TIFF)."""
    try:
        from PIL import Image
        import pytesseract
    except ImportError as e:
        raise ImportError(f"OCR dependencies not installed: {e}")

    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image, lang="eng")


def extract_text_with_ocr(file_bytes: bytes, filename: str) -> tuple[str, bool]:
    """
    Smart text extraction: tries standard extraction first, falls back to OCR.
    Returns (extracted_text, used_ocr_flag).
    """
    name = filename.lower()

    # Image files → always OCR
    if name.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp")):
        return ocr_image(file_bytes), True

    # PDF → try standard first, fallback to OCR
    if name.endswith(".pdf"):
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        standard_text = "\n\n".join(text_parts)

        # If standard extraction yields very little, try OCR
        if len(standard_text.strip()) < 50 * max(1, len(text_parts) if text_parts else 1):
            if is_scanned_pdf(file_bytes):
                try:
                    ocr_text = ocr_pdf(file_bytes)
                    if len(ocr_text.strip()) > len(standard_text.strip()):
                        return ocr_text, True
                except Exception as e:
                    logger.warning(f"OCR fallback failed: {e}")

        return standard_text, False

    # DOCX
    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        text = "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
        return text, False

    # TXT
    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace"), False

    raise ValueError(f"Unsupported file type: {name}")
