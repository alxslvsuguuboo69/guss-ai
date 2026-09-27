import json
import requests
from flask import current_app

class OpenRouterService:
    @staticmethod
    def stream_chat_completion(messages: list):
        api_key = current_app.config.get("OPENROUTER_API_KEY")
        if not api_key:
            yield f"data: {json.dumps({'choices': [{'delta': {'content': 'Error: Falta la API Key de OpenRouter en Render.'}}]})}\n\n"
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://guss-ai.onrender.com",
            "X-Title": "Guss AI",
            "Content-Type": "application/json"
        }

        payload = {
            "model": current_app.config.get("DEFAULT_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
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
                error_msg = f"Error {response.status_code} de OpenRouter."
                yield f"data: {json.dumps({'choices': [{'delta': {'content': error_msg}}]})}\n\n"
                return

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        yield f"data: {data_str}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'choices': [{'delta': {'content': f'Error en el servidor: {str(e)}'}}]})}\n\n"
