import os
from groq import Groq

# Initialize the Groq client
def _get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in environment or .env file.")
    return Groq(api_key=api_key)

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Transcribes a single audio chunk using the Groq Whisper API.
    """
    client = _get_client()
    print(f"Uploading {chunk_path} to Groq Whisper API...")
    
    with open(chunk_path, "rb") as audio_file:
        # We prompt it in English if language is english, else just let Whisper autodetect
        prompt = "This is a video transcript."
        if language.lower() == "hinglish":
            prompt = "This is a video transcript containing Hindi and English."
            
        response = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            prompt=prompt
        )
        
    return response.text.strip()

def get_transcript(chunks: list, language: str = "english") -> str:
    """
    Given a list of chunk paths, returns the full transcript by calling Groq API on each chunk.
    """
    full_transcript = ""
    
    for i, chunk_path in enumerate(chunks):
        print(f"\n[Transcriber] Processing chunk {i + 1}/{len(chunks)} ...")
        text = transcribe_chunk(chunk_path, language)
        full_transcript += text + " "
        
    return full_transcript.strip()
