from flask import Blueprint, request, jsonify, render_template
from app.services.llm import chat_completion

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/")
def index():
    return render_template("index.html")

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "El mensaje no puede estar vacío"}), 400

    messages = [
        {"role": "system", "content": "Eres Guss AI, un asistente útil, claro y amable."},
        {"role": "user", "content": user_message},
    ]

    try:
        reply = chat_completion(messages)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
