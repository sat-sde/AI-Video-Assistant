import os
from sarvamai import SarvamAI

def generate_tts(text: str, target_language: str = "hi-IN", speaker: str = "meera") -> dict:
    """
    Calls Sarvam AI Text-to-Speech API.
    Returns the audio data (usually base64 encoded).
    """
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is missing from environment variables.")
        
    client = SarvamAI(api_subscription_key=api_key)
    
    print(f"Generating TTS for language {target_language} with speaker {speaker}...")
    response = client.text.text_to_speech(
        text=text,
        target_language_code=target_language,
        speaker=speaker
    )
    
    return response
