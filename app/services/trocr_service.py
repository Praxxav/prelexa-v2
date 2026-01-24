import logging
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

logger = logging.getLogger(__name__)

class TrOCRService:
    _instance = None
    _model = None
    _processor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrOCRService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        """
        Load TrOCR model and processor.
        Warning: This model is heavy (~1.5GB).
        """
        try:
            logger.info("Loading TrOCR model (microsoft/trocr-base-handwritten)...")
            # Use GPU if available, else CPU
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")

            self._processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
            self._model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten').to(self.device)
            logger.info("TrOCR model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load TrOCR model: {e}")
            raise

    def perform_ocr(self, image: Image.Image) -> str:
        """
        Perform OCR on a single PIL Image.
        Handles large images by slicing them into horizontal strips.
        """
        if not self._model or not self._processor:
            logger.error("TrOCR model not initialized.")
            return ""

        try:
            # Ensure RGB
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            width, height = image.size
            
            # If image is small enough (likely a cropped line), process directly
            # TrOCR native resolution is 384x384, but can handle aspect ratios.
            # However, for full pages (e.g. A4 at 150dpi is ~1200x1700), we must slice.
            if height <= 400:
                return self._inference_single_patch(image)

            # --- Slicing Logic for Full Pages ---
            # We slice the image into horizontal strips of ~384px height (simulating text blocks)
            # We add overlap to avoid cutting through a line of text.
            
            slice_height = 300 # Slightly less than 384 to be safe
            overlap = 50
            results = []
            
            y = 0
            while y < height:
                # Calculate slice coordinates
                bottom = min(y + slice_height, height)
                # Ensure we don't carry over too much noise, straightforward crop
                box = (0, y, width, bottom)
                
                slice_img = image.crop(box)
                
                # Check if slice is not just empty whitespace (simple heuristic)
                if self._has_content(slice_img):
                    text = self._inference_single_patch(slice_img)
                    if text.strip():
                        results.append(text)
                
                # Move window
                if bottom == height:
                    break
                y += (slice_height - overlap)
                
            return "\n".join(results)

        except Exception as e:
            logger.error(f"Error during TrOCR inference: {e}")
            return ""

    def _inference_single_patch(self, image: Image.Image) -> str:
        """Helper to run inference on a specific image patch."""
        try:
            pixel_values = self._processor(images=image, return_tensors="pt").pixel_values.to(self.device)
            generated_ids = self._model.generate(pixel_values, max_new_tokens=256) # Increase tokens for denser slices
            generated_text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return generated_text
        except Exception as e:
            logger.warning(f"Patch inference failed: {e}")
            return ""

    def _has_content(self, image: Image.Image) -> bool:
        """
        Simple check to skip empty white slices.
        """
        try:
            # Convert to grayscale and get extrema
            extrema = image.convert("L").getextrema()
            # If min and max are close to 255 (white), it's empty
            if extrema[0] > 240: 
                return False
            return True
        except:
            return True

# Singleton instance for easy import
try:
    trocr_service = TrOCRService()
except Exception as e:
    logger.error(f"Could not initialize TrOCRService at module level: {e}")
    trocr_service = None
