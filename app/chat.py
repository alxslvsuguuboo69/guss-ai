from flask import Blueprint, render_template, request, jsonify
from app.services.openrouter import OpenRouterService

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/")
def index():
    return render_template("index.html")

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No se proporcionaron mensajes."}), 400

    try:
        reply = OpenRouterService.send_chat_completion(messages)
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
