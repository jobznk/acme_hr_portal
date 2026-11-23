import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def extract_text_from_image(image_path: str) -> str:
    """Read text from a PNG or JPG image using Tesseract OCR."""
    image = Image.open(image_path)
    return pytesseract.image_to_string(image).strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """Read text from a normal PDF, or use OCR if the PDF is scanned."""
    # 1. Try reading normal selectable text first
    pages = PyPDFLoader(pdf_path).load()
    normal_text = "\n\n".join(page.page_content for page in pages).strip()
    if normal_text:
        return normal_text

    # 2. If empty (scanned PDF), convert pages to images and run OCR
    scanned_images = convert_from_path(pdf_path)
    ocr_pages = [pytesseract.image_to_string(img) for img in scanned_images]
    return "\n\n".join(ocr_pages).strip()


def extract_text_from_file(file_path: str) -> str:
    """Pick the right text reader based on the file extension."""
    extension = os.path.splitext(file_path)[1].lower()

    if extension in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_path)

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    # Default: plain .txt file
    docs = TextLoader(file_path).load()
    return "\n\n".join(doc.page_content for doc in docs).strip()
