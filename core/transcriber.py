import os
import time
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def _transcribe_with_gemini(audio_path: str, language: str) -> str:
    """Uploads the audio file to Gemini and asks it to transcribe."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in environment or .env file.")

    print(f"Uploading {audio_path} to Gemini...")
    audio_file = genai.upload_file(path=audio_path)
    
    try:
        # Wait for the file to be processed if necessary (usually instant for audio, but good practice)
        while audio_file.state.name == "PROCESSING":
            print("Gemini is processing the file...")
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
            
        if audio_file.state.name == "FAILED":
            raise ValueError(f"Gemini failed to process the audio file.")
            
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = "Please provide a highly accurate, word-for-word transcription of this audio."
        if language.lower() == "hinglish":
            prompt = "Please transcribe this audio. It may contain a mix of Hindi and English. Please translate the entire transcript into English, providing a highly accurate English transcription."
            
        print("Generating transcript with Gemini...")
        response = model.generate_content([prompt, audio_file])
        return response.text.strip()
    finally:
        # Clean up the file from Google's servers
        try:
            genai.delete_file(audio_file.name)
        except Exception as e:
            print(f"Warning: Failed to delete remote Gemini file: {e}")

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Transcribes the audio using the Gemini API.
    (Kept the function name 'transcribe_chunk' for compatibility, though it processes the full file now).
    """
    return _transcribe_with_gemini(chunk_path, language)

def get_transcript(chunks: list, language: str = "english") -> str:
    """
    Given a list of chunk paths (now just a list with 1 path), returns the full transcript.
    """
    full_transcript = ""
    
    for i, chunk_path in enumerate(chunks):
        print(f"\n[Transcriber] Processing file {i + 1}/{len(chunks)} ...")
        text = transcribe_chunk(chunk_path, language)
        full_transcript += text + " "
        
    return full_transcript.strip()
