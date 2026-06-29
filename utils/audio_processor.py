import yt_dlp
import os

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

    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Downloading audio from {url}...")
            info_dict = ydl.extract_info(url, download=True)
            # Find the actual downloaded file (yt-dlp changes the extension after conversion)
            title = info_dict.get('title', 'video')
            # Look for the downloaded mp3 file in the directory
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith('.mp3'):
                    return os.path.join(DOWNLOAD_DIR, f)
            raise FileNotFoundError("Audio file not found after download.")
    except Exception as e:
        print(f"Error downloading YouTube video: {e}")
        raise e

def process_input(source: str):
    """
    Downloads audio from YouTube and returns the file path.
    Since we use Gemini API, we no longer need to chunk the audio!
    """
    if "youtube.com" in source or "youtu.be" in source:
        audio_path = download_youtube_audio(source)
    else:
        audio_path = source
        
    return [audio_path] # Return as a list with one item for compatibility with transcriber
