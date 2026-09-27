import requests
from flask import current_app

class OpenRouterService:
    @staticmethod
    def send_chat_completion(messages: list) -> str:
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("La clave API de OpenRouter no está configurada.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Guss AI",
            "Content-Type": "application/json"
        }

        payload = {
            "model": current_app.config["DEFAULT_MODEL"],
            "messages": messages
        }

        response = requests.post(
            current_app.config["OPENROUTER_BASE_URL"],
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Error al comunicarse con OpenRouter")
            raise RuntimeError(f"Error {response.status_code}: {error_msg}")

        data = response.json()
        return data["choices"][0]["message"]["content"]
