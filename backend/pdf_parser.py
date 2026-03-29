import io
import PyPDF2

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text content from a PDF file provided as bytes."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page_num in range(len(reader.pages)):
            page_text = reader.pages[page_num].extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"Failed to read PDF: {e}")
        return "Failed to extract text from PDF."
