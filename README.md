# 🎬 AI Video Assistant

An intelligent video analysis pipeline that downloads audio from YouTube (or local files), transcribes it using AI, extracts structured insights, and lets you chat with the content via a RAG-powered assistant — all through a modern React dashboard.

---

## ✨ Features

- 🔊 **Audio Acquisition** — Download audio directly from YouTube URLs or process local audio/video files
- 📝 **AI Transcription** — Transcribe audio using OpenAI Whisper (local, offline) or Sarvam AI (for Hinglish)
- 🏷️ **Title Generation** — Auto-generate a professional title for the meeting/video
- 📋 **Smart Summarization** — Produce structured bullet-point summaries using Mistral AI
- 🔍 **Insight Extraction** — Extract Action Items, Key Decisions, and Open Questions
- 🧠 **RAG Chat** — Ask questions about the video content powered by a ChromaDB vector store + Mistral LLM
- 🖥️ **React Dashboard** — Beautiful, responsive single-page UI with tabbed explorer and persistent chat window

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend (Vite)                 │
│              http://localhost:5173                       │
└──────────────────────┬──────────────────────────────────┘
                       │  fetch() REST API calls
                       ▼
┌─────────────────────────────────────────────────────────┐
│               Flask API Server (Python)                 │
│              http://localhost:5001                       │
│   POST /api/pipeline    POST /api/chat                  │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────┐   ┌───────────────────────┐
│  Audio Pipeline  │   │   LLM / RAG Engine    │
│  yt-dlp + pydub  │   │  Mistral + LangChain  │
│  Whisper / Sarvam│   │  ChromaDB + HuggingFace│
└──────────────────┘   └───────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, Vite, Tailwind CSS v4, Lucide React |
| **Backend API** | Python, Flask, Flask-CORS |
| **Audio** | yt-dlp, pydub, FFmpeg |
| **Transcription** | OpenAI Whisper (local), Sarvam AI (Hinglish) |
| **LLM** | Mistral AI (`mistral-small-latest`) via LangChain |
| **RAG / Embeddings** | ChromaDB, HuggingFace `all-MiniLM-L6-v2` |
| **Orchestration** | LangChain LCEL |

---

## 📁 Project Structure

```
AI-Video-Assistant/
├── api_server.py          # Flask REST API (bridges frontend ↔ backend)
├── main.py                # CLI entry point for the pipeline
├── Requirements.txt       # Python dependencies
├── .env                   # API keys (not committed)
│
├── core/
│   ├── transcriber.py     # Whisper + Sarvam AI transcription
│   ├── summarizer.py      # Map-reduce summarization (Mistral)
│   ├── extractor.py       # Action items, decisions, questions
│   ├── rag_engine.py      # RAG chain builder + question answering
│   └── vector_store.py    # ChromaDB vector store management
│
├── utils/
│   └── audio_processor.py # YouTube download + audio chunking
│
└── frontend/
    ├── src/
    │   ├── App.jsx         # Main React dashboard component
    │   ├── main.jsx        # React entry point
    │   └── index.css       # Tailwind CSS import
    ├── vite.config.js      # Vite + Tailwind plugin config
    └── package.json
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [FFmpeg](https://ffmpeg.org/download.html) installed and on your `$PATH`
- [uv](https://github.com/astral-sh/uv) (Python package manager, used by this project)

### 1. Clone the Repository

```bash
git clone https://github.com/sat-sde/AI-Video-Assistant.git
cd AI-Video-Assistant
```

### 2. Set Up Python Environment

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -r Requirements.txt
```

### 3. Configure API Keys

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_mistral_api_key_here
SARVAM_API_KEY=your_sarvam_api_key_here   # Only needed for Hinglish transcription
```

- Get a Mistral API key at [console.mistral.ai](https://console.mistral.ai)
- Get a Sarvam API key at [sarvam.ai](https://sarvam.ai) *(only needed for Hinglish)*

### 4. Set Up the Frontend

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Running the App

You need to run **two servers** simultaneously — the Flask backend and the Vite frontend.

**Terminal 1 — Backend API:**
```bash
.venv/bin/python api_server.py
# → Running on http://localhost:5001
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# → Running on http://localhost:5173
```

Then open **http://localhost:5173** in your browser.

---

## 🖥️ Using the Dashboard

1. **Paste** a YouTube URL or local file path into the Source input
2. **Select** the language (`English` or `Hinglish`)
3. **Click** `Analyze Video` — the pipeline will run (this takes a few minutes for audio download + transcription)
4. Once complete, explore the results across three tabs:
   - **Summary** — structured bullet-point summary
   - **Insights** — action items, key decisions, open questions
   - **Transcript** — full raw transcript
5. **Chat** with the video content using the RAG assistant on the right panel

---

## 🖥️ CLI Usage

Alternatively, run the pipeline directly from the terminal:

```bash
.venv/bin/python main.py
# Enter YouTube URL or local file path: https://youtube.com/watch?v=...
# Language (english/hinglish): english
```

---

## 🔌 API Reference

### `POST /api/pipeline`

Runs the full processing pipeline.

**Request:**
```json
{
  "source": "https://youtube.com/watch?v=VIDEO_ID",
  "language": "english"
}
```

**Response:**
```json
{
  "title": "Meeting Title",
  "transcript": "Full transcript text...",
  "summary": "Structured summary...",
  "action_items": "1. Task...",
  "key_decisions": "1. Decision...",
  "open_questions": "1. Question...",
  "session_id": "uuid-string"
}
```

### `POST /api/chat`

Ask a question against the RAG engine.

**Request:**
```json
{
  "session_id": "uuid-from-pipeline-response",
  "question": "What were the main takeaways?"
}
```

**Response:**
```json
{
  "answer": "Based on the transcript, the main takeaways were..."
}
```

---

## ⚠️ Notes

- **Whisper runs on CPU** by default — transcription may take several minutes for long videos
- **Port 5001** is used for the Flask API to avoid conflict with macOS AirPlay (which uses 5000)
- The **RAG session** is stored in memory — restarting the API server clears all sessions
- Audio files are downloaded to the `downloades/` directory and are **not committed** to Git

---

## 📄 License

MIT License — feel free to use, modify, and distribute.
