import yt_dlp
import os
import uuid
import math
from pydub import AudioSegment

DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def _clean_download_dir():
    """Remove old files from the download directory to avoid stale data."""
    for f in os.listdir(DOWNLOAD_DIR):
        filepath = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(filepath):
            os.remove(filepath)

def download_youtube_audio(url: str) -> str:
    _clean_download_dir()

    safe_name = str(uuid.uuid4())[:8]
    output_path = os.path.join(DOWNLOAD_DIR, f"{safe_name}.%(ext)s")
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android", "web"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    # If the user has provided cookies via environment variable (to bypass bot detection)
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if cookies_content:
        # If using desktop cookies, spoofing mobile clients causes format errors, so remove it
        if "extractor_args" in ydl_opts:
            del ydl_opts["extractor_args"]
            
        cookies_file_path = os.path.join(DOWNLOAD_DIR, "youtube_cookies.txt")
        with open(cookies_file_path, "w") as f:
            f.write(cookies_content)
        ydl_opts["cookiefile"] = cookies_file_path
        print("[AudioProcessor] Using YOUTUBE_COOKIES to bypass bot detection.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading audio from {url}...")
            ydl.extract_info(url, download=True)
            # Find the actual downloaded file
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith('.mp3'):
                    return os.path.join(DOWNLOAD_DIR, f)
            raise FileNotFoundError("Audio file not found after download.")
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        raise e

def chunk_audio(file_path: str, chunk_length_ms: int = 10 * 60 * 1000) -> list:
    """Chunks audio into smaller pieces to bypass API size limits (e.g. OpenAI 25MB limit)."""
    print(f"Chunking audio: {file_path}")
    audio = AudioSegment.from_file(file_path)
    chunks = []
    
    total_length = len(audio)
    num_chunks = math.ceil(total_length / chunk_length_ms)
    
    for i in range(num_chunks):
        start_time = i * chunk_length_ms
        end_time = min((i + 1) * chunk_length_ms, total_length)
        chunk = audio[start_time:end_time]
        
        chunk_name = f"{file_path}_chunk_{i}.mp3"
        chunk.export(chunk_name, format="mp3")
        chunks.append(chunk_name)
        
    print(f"Audio chunked into {len(chunks)} pieces.")
    return chunks

def process_input(source: str):
    """
    Downloads audio from YouTube and returns a list of chunked file paths.
    """
    if "youtube.com" in source or "youtu.be" in source:
        audio_path = download_youtube_audio(source)
    else:
        audio_path = source
        
    # Return chunked paths
    return chunk_audio(audio_path)
