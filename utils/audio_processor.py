import yt_dlp
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import os
import re
import uuid

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def _clean_download_dir():
    """Remove old files from the download directory to avoid stale data."""
    for f in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(filepath):
            os.remove(filepath)

def extract_video_id(url: str) -> str:
    pattern = r"(?:v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(url: str) -> str | None:
    video_id = extract_video_id(url)
    if not video_id:
        return None
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # Try finding en or hi
        try:
            transcript = transcript_list.find_transcript(["en", "hi"])
        except Exception:
            # Fallback to translate
            available = list(transcript_list._manually_created_transcripts.keys()) + list(transcript_list._generated_transcripts.keys())
            if not available:
                return None
            transcript = transcript_list.find_transcript(available)
            if 'en' in transcript.translation_languages:
                transcript = transcript.translate('en')
                
        fetched = transcript.fetch()
        text = " ".join([getattr(t, "text", "") for t in fetched])
        # Clean up text
        text = text.replace('\n', ' ')
        return re.sub(r'\s+', ' ', text).strip()
        
    except (NoTranscriptFound, TranscriptsDisabled):
        print(f"[AudioProcessor] Transcripts disabled or not found for {video_id}")
        return None
    except Exception as e:
        print(f"[AudioProcessor] Error fetching transcript: {e}")
        return None

def download_youtube_audio(url: str) -> str:
    _clean_download_dir()
    safe_name = str(uuid.uuid4())[:8]
    output_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.%(ext)s")
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': output_path,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'web']
            }
        },
        'js_runtimes': {'node': {}},
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        "quiet": True,
        "no_warnings": True,
    }
    
    # If the user has provided cookies via environment variable (to bypass bot detection)
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        # Prevent bot blocks: Don't spoof mobile clients when using desktop browser cookies
        if "extractor_args" in ydl_opts:
            del ydl_opts["extractor_args"]
            
        cookies_file_path = os.path.join(DOWNLOAD_DIR, "youtube_cookies.txt")
        with open(cookies_file_path, "w") as f:
            f.write(cookies_content)
        ydl_opts["cookiefile"] = cookies_file_path
        print("[AudioProcessor] Using YOUTUBE_COOKIES to bypass bot detection.")
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace('.webm', '.wav').replace('.m4a', '.wav')
        
        # If prepare_filename fails due to uuid, fallback to finding the file
        if not os.path.exists(filename):
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith('.wav'):
                    return os.path.join(DOWNLOAD_DIR, f)
        return filename

def convert_to_wav(input_path: str) -> str:
    filename = os.path.splitext(os.path.basename(input_path))[0] + '.wav'
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav")
    return output_path

def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_file(wav_path)
    # Ensure it's 16000Hz mono as Whisper prefers this format
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks

def process_input(source: str):
    """
    Returns (transcript_text, None) if YouTube captions found.
    Returns (None, chunks) if audio needs Whisper transcription.
    """
    if "youtube.com" in source or "youtu.be" in source:
        print("Trying YouTube captions (fast path)...")
        transcript = get_youtube_transcript(source)
        if transcript:
            print("Captions found — skipping audio download.")
            return transcript, None

        print("No captions found — downloading audio for Whisper...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s).")
    return None, chunks
