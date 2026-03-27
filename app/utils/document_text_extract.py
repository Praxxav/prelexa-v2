import PyPDF2
import docx
import os
import logging
import io
from typing import Optional, List
from pdf2image import convert_from_path
from PIL import Image
# from app.services.trocr_service import trocr_service

async def perform_ocr_offline(image: Image.Image) -> str:
    """
    TrOCR model not available in production (removed to reduce container size).
    OCR for images will be handled by Gemini Vision API instead.
    """
    # if not trocr_service:
    #     logging.error("TrOCR Service is not available.")
    #     return ""
    # 
    # return trocr_service.perform_ocr(image)
    logging.info("Local OCR not available - use Gemini Vision API for image text extraction")
    return ""

async def extract_text_from_file(file_path: str) -> Optional[str]:
    """
    Extract text content from various document formats.
    Supports PDF (native + Offline OCR fallback), DOCX, TXT, and Images (PNG/JPG).
    """
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # ---------------------------
        # PDF HANDLING
        # ---------------------------
        if file_extension == '.pdf':
            text = ""
            try:
                # 1. Try Native Extraction
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                
                # 2. Check completeness (heuristic: < 50 chars per page might be a scan)
                if len(text.strip()) < 50:
                    logging.info("PDF text too short, attempting Offline OCR...")
                    images = convert_from_path(file_path)
                    ocr_text = ""
                    for img in images:
                        ocr_text += await perform_ocr_offline(img) + "\n"
                    
                    if len(ocr_text) > len(text):
                        text = ocr_text

            except Exception as pdf_err:
                logging.warning(f"Native PDF extraction failed, trying OCR: {pdf_err}")
                # Fallback to OCR if native fails entirely
                try:
                    images = convert_from_path(file_path)
                    for img in images:
                        text += await perform_ocr_offline(img) + "\n"
                except Exception as ocr_err:
                    logging.error(f"PDF OCR failed: {ocr_err}")
            
            return text
            
        # ---------------------------
        # WORD DOC
        # ---------------------------
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
            
        # ---------------------------
        # TEXT FILE
        # ---------------------------
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

        # ---------------------------
        # IMAGES (OCR)
        # ---------------------------
        elif file_extension in ['.png', '.jpg', '.jpeg', '.webp']:
            try:
                image = Image.open(file_path)
                return await perform_ocr_offline(image)
            except Exception as img_err:
                logging.error(f"Image OCR failed: {img_err}")
                return None
                
        else:
            logging.error(f"Unsupported file type: {file_extension}")
            return None
            
    except Exception as e:
        logging.error(f"Error extracting text from file: {e}")
        return None
