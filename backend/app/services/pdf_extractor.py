import fitz  # PyMuPDF
from io import BytesIO

def extract_text_from_pdf(file_bytes: bytes) -> str:
   
    text_parts = []
    with fitz.open(stream=BytesIO(file_bytes), filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text("text")  # extract plain text
            if page_text:
                text_parts.append(page_text)

    # join pages and clean whitespace
    text = "\n".join(text_parts).strip()
    text = " ".join(text.split())  
    return text
