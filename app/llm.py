import requests
from flask import current_app

def chat_completion(messages: list[dict]) -> str:
    api_key = current_app.config["OPENROUTER_API_KEY"]
    model = current_app.config["OPENROUTER_MODEL"]
    base_url = current_app.config["OPENROUTER_BASE_URL"]

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY no está configurada")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guss-ai.onrender.com",
        "X-Title": "Guss AI",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]
