python
import os
import urllib.request
import urllib.error
import json
from flask import Flask, request, jsonify, render_template

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)

# ==========================================
# CONFIGURACIÓN
# ==========================================

API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELO = "openrouter/free"

# ==========================================
# MEMORIA DE CONVERSACIÓN
# ==========================================

historial = []

# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# CHAT
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    datos_web = request.get_json()

    if not datos_web:
        return jsonify({
            "error": "No se recibieron datos."
        }), 400

    mensaje = datos_web.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({
            "error": "El mensaje está vacío."
        }), 400

    # Guardar mensaje del usuario
    historial.append({
        "role": "user",
        "content": mensaje
    })

    # Limitar memoria para no mandar una conversación infinita
    historial_reciente = historial[-20:]

    # Personalidad de Guss
    mensajes = [
        {
            "role": "system",
            "content": """
Eres Guss, una inteligencia artificial amigable, útil y conversacional.

Respondes principalmente en español.

Tienes memoria de la conversación actual. 
Debes utilizar el contexto de los mensajes anteriores para mantener conversaciones coherentes.

No repitas innecesariamente información que ya conoces.

Si el usuario te cuenta su nombre, preferencias o información durante la conversación,
puedes utilizarla posteriormente dentro de esta misma conversación.

Sé natural y conversa como una IA moderna.
"""
        }
    ]

    # Añadir memoria
    mensajes.extend(historial_reciente)

    datos = {
        "model": MODELO,
        "messages": mensajes
    }

    try:

        json_datos = json.dumps(datos).encode("utf-8")

        peticion = urllib.request.Request(
            API_URL,
            data=json_datos,
            method="POST"
        )

        peticion.add_header(
            "Authorization",
            f"Bearer {API_KEY}"
        )

        peticion.add_header(
            "Content-Type",
            "application/json"
        )

        with urllib.request.urlopen(peticion) as respuesta:

            resultado = json.loads(
                respuesta.read().decode("utf-8")
            )

        texto_guss = (
            resultado["choices"][0]["message"]["content"]
        )

        # Guardar respuesta de Guss
        historial.append({
            "role": "assistant",
            "content": texto_guss
        })

        return jsonify({
            "respuesta": texto_guss
        })

    except urllib.error.HTTPError as e:

        cuerpo = e.read().decode("utf-8")

        # Si OpenRouter falla, quitamos el último mensaje
        # para evitar guardar mensajes que nunca tuvieron respuesta.
        if historial and historial[-1]["role"] == "user":
            historial.pop()

        return jsonify({
            "error": f"Error HTTP {e.code}: {cuerpo}"
        }), 500

    except Exception as e:

        if historial and historial[-1]["role"] == "user":
            historial.pop()

        return jsonify({
            "error": str(e)
        }), 500


# ==========================================
# INICIO LOCAL
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
```
