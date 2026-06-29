"""
Flask API server — connects the React frontend to the Python backend pipeline.
"""

import uuid
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Use abspath to resolve the correct path regardless of working directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

print(f"[Server] BASE_DIR={BASE_DIR}")
print(f"[Server] FRONTEND_DIST={FRONTEND_DIST}")
print(f"[Server] dist exists={os.path.isdir(FRONTEND_DIST)}")

app = Flask(__name__)
CORS(app)

# In-memory store for RAG chains keyed by session_id
_sessions = {}


# ── Health check ─────────────────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "dist_exists": os.path.isdir(FRONTEND_DIST)})


# ── API Routes ────────────────────────────────────────────────────────────────
@app.route("/api/pipeline", methods=["POST"])
def run_pipeline():
    """Run the full AI Video Assistant pipeline using Gemini API."""
    from utils.audio_processor import process_input
    from core.transcriber import get_transcript
    from core.summarizer import summarize, generate_title
    from core.extractor import extract_action_items, extract_key_decisions, extract_questions
    from core.rag_engine import build_rag_chain

    data = request.get_json()
    source = data.get("source", "").strip()
    language = data.get("language", "english").strip()

    if not source:
        return jsonify({"error": "source is required"}), 400

    try:
        print(f"[Pipeline] Starting for source={source}, language={language}")

        print("[Pipeline] Step 1/6: Processing audio...")
        chunks = process_input(source)

        print("[Pipeline] Step 2/6: Transcribing with Gemini API...")
        transcript = get_transcript(chunks, language)

        print("[Pipeline] Step 3/6: Generating title...")
        title = generate_title(transcript)

        print("[Pipeline] Step 4/6: Summarizing...")
        summary = summarize(transcript)

        print("[Pipeline] Step 5/6: Extracting insights...")
        action_items = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        print("[Pipeline] Step 6/6: Building RAG engine...")
        rag_chain = build_rag_chain(transcript)

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
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """Ask a question against a previously built RAG chain."""
    from core.rag_engine import ask_question

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


# ── Serve React SPA (must be LAST to not shadow API routes) ──────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    """Serve built React app. Falls back to index.html for client-side routing."""
    # Check if a real file exists (JS, CSS, images, etc.)
    requested_file = os.path.join(FRONTEND_DIST, path)
    if path and os.path.isfile(requested_file):
        return send_from_directory(FRONTEND_DIST, path)
    # Otherwise serve index.html (React handles routing)
    index = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.isfile(index):
        return send_from_directory(FRONTEND_DIST, "index.html")
    return f"<h1>Frontend not built</h1><p>dist not found at: {FRONTEND_DIST}</p>", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[Server] Starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
