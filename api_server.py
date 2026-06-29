"""
Flask API server that bridges the React frontend to the Python backend pipeline.

Endpoints:
  POST /api/pipeline  — runs the full pipeline (audio → transcript → insights → RAG)
  POST /api/chat      — asks a question against the RAG chain for a given session
"""

import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

app = Flask(__name__)
CORS(app)  # Allow frontend on localhost:5173 to call this API

# In-memory store for RAG chains keyed by session_id
_sessions = {}


@app.route("/api/pipeline", methods=["POST"])
def run_pipeline():
    """Run the full AI Video Assistant pipeline."""
    data = request.get_json()
    source = data.get("source", "").strip()
    language = data.get("language", "english").strip()

    if not source:
        return jsonify({"error": "source is required"}), 400

    try:
        print(f"[Pipeline] Starting for source={source}, language={language}")

        # Step 1: Audio processing
        print("[Pipeline] Step 1/6: Processing audio...")
        chunks = process_input(source)

        # Step 2: Transcription
        print("[Pipeline] Step 2/6: Transcribing...")
        transcript = transcribe_all(chunks, language)

        # Step 3: Title generation
        print("[Pipeline] Step 3/6: Generating title...")
        title = generate_title(transcript)

        # Step 4: Summarization
        print("[Pipeline] Step 4/6: Summarizing...")
        summary = summarize(transcript)

        # Step 5: Insight extraction
        print("[Pipeline] Step 5/6: Extracting insights...")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        # Step 6: RAG engine
        print("[Pipeline] Step 6/6: Building RAG engine...")
        rag_chain = build_rag_chain(transcript)

        # Store the RAG chain in memory with a session ID
        session_id = str(uuid.uuid4())
        _sessions[session_id] = rag_chain

        print(f"[Pipeline] Complete! session_id={session_id}")

        return jsonify({
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items,
            "key_decisions": decisions,
            "open_questions": questions,
            "session_id": session_id,
        })

    except Exception as e:
        print(f"[Pipeline] Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """Ask a question against a previously built RAG chain."""
    data = request.get_json()
    session_id = data.get("session_id", "")
    question = data.get("question", "").strip()

    if not session_id or session_id not in _sessions:
        return jsonify({"error": "Invalid or expired session_id"}), 400
    if not question:
        return jsonify({"error": "question is required"}), 400

    try:
        rag_chain = _sessions[session_id]
        answer = ask_question(rag_chain, question)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"[Chat] Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
