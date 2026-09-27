import json
import requests
from flask import current_app


class OpenRouterService:

    @staticmethod
    def stream_chat_completion(messages: list):
        api_key = current_app.config.get("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "La clave API de OpenRouter no está configurada."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://guss-ai.onrender.com",
            "X-Title": "Guss AI",
            "Content-Type": "application/json"
        }

        payload = {
            "model": current_app.config["DEFAULT_MODEL"],
            "messages": messages,
            "stream": True
        }

        try:
            response = requests.post(
                current_app.config["OPENROUTER_BASE_URL"],
                headers=headers,
                json=payload,
                stream=True,
                timeout=60
            )

            if response.status_code != 200:
                try:
                    error_data = response.json()
                except ValueError:
                    error_data = {
                        "error": response.text
                    }

                yield f"data: {json.dumps(error_data)}\n\n"
                return

            for line in response.iter_lines(decode_unicode=True):

                if not line:
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]

                    if data_str == "[DONE]":
                        break

                    yield f"data: {data_str}\n\n"

        except requests.RequestException as e:
            error_data = {
                "error": f"Error de conexión con OpenRouter: {str(e)}"
            }

            yield f"data: {json.dumps(error_data)}\n\n"
