import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from various forms of YouTube URLs."""
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/shorts\/([0-9A-Za-z_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_youtube_captions(url: str, language: str = "english") -> str:
    """
    Attempts to fetch captions natively from YouTube.
    Maps 'english' to 'en' and 'hinglish' to 'hi'/'en'.
    Returns the transcript as a single string, or None if no captions exist.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return None

    try:
        # Determine language code preferences
        lang_codes = ['en']
        if language.lower() == "hinglish" or language.lower() == "hindi":
            lang_codes = ['hi', 'en-IN', 'en']

        # Fetch the transcript list from YouTube
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # Try to find a transcript in the preferred languages
        transcript = None
        try:
            transcript = transcript_list.find_transcript(lang_codes)
        except Exception:
            # If preferred languages aren't found, just grab the first available transcript
            # and attempt to translate it to English natively via YouTube's translate API
            available_transcripts = list(transcript_list._manually_created_transcripts.keys()) + list(transcript_list._generated_transcripts.keys())
            if not available_transcripts:
                return None
            transcript = transcript_list.find_transcript(available_transcripts)
            if 'en' in transcript.translation_languages:
                transcript = transcript.translate('en')

        if transcript:
            fetched = transcript.fetch()
            formatter = TextFormatter()
            text = formatter.format_transcript(fetched)
            
            # Clean up the text by removing excessive newlines
            text = text.replace('\n', ' ')
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
    except Exception as e:
        print(f"[CaptionFetcher] Could not fetch native captions for {video_id}: {e}")
        return None
        
    return None
