import yt_dlp
from pydub import AudioSegment
import os
import glob

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
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Replace ANY extension with .wav (FFmpeg post-processor outputs .wav)
        base = os.path.splitext(ydl.prepare_filename(info))[0]
        filename = base + ".wav"

    # Fallback: if the exact filename doesn't exist, find the .wav in the dir
    if not os.path.isfile(filename):
        wav_files = glob.glob(os.path.join(DOWNLOAD_DIR, "*.wav"))
        # Exclude chunk files from a previous run
        wav_files = [f for f in wav_files if "_chunk_" not in f]
        if wav_files:
            filename = wav_files[0]
        else:
            raise FileNotFoundError(
                f"No .wav file found in {DOWNLOAD_DIR} after download. "
                "Check that ffmpeg is installed and yt-dlp downloaded successfully."
            )

    print(f"Audio downloaded: {filename} ({os.path.getsize(filename) / 1024 / 1024:.1f} MB)")
    return filename



def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


