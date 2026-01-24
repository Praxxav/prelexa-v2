import os
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

def download_model():
    print("Checking/Downloading TrOCR model...")
    # This will download the model to the huggingface cache directory if not present
    TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
    VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
    print("Model loaded successfully.")

if __name__ == "__main__":
    download_model()
