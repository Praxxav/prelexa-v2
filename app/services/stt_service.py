import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def transcribe_audio_file(file_path: str) -> str:
    """Transcribe an audio file using Gemini 1.5 Flash"""
    try:
        # Upload the file to Gemini
        audio_file = genai.upload_file(file_path)
        
        # Initialize model
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Generate content
        response = model.generate_content(
            [
                "Transcribe this audio file accurately. Output only the transcription, no other text.",
                audio_file
            ]
        )
        
        return response.text
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""
