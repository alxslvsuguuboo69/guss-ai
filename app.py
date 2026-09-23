import os
import urllib.request
import urllib.error
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELO = "openrouter/free"


# Página principal
@app.route("/")
def inicio():
    return """
    <h1>Guss AI 🤖</h1>
    <p>El servidor está funcionando correctamente.</p>
    <p>La API de Guss está disponible en /chat</p>
    """


# Endpoint para hablar con Guss
@app.route("/chat", methods=["POST"])
def chat():

    datos_web = request.json
    mensaje = datos_web.get("mensaje", "")

    if not mensaje:
        return jsonify({"error": "El mensaje está vacío"}), 400

    datos = {
        "model": MODELO,
        "messages": [
            {
                "role": "system",
                "content": "Eres Guss, una IA amigable que responde en español."
            },
            {
                "role": "user",
                "content": mensaje
            }
        ]
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

        texto_guss = resultado["choices"][0]["message"]["content"]

        return jsonify({
            "respuesta": texto_guss
        })

    except urllib.error.HTTPError as e:

        cuerpo = e.read().decode("utf-8")

        return jsonify({
            "error": f"Error HTTP {e.code}: {cuerpo}"
        }), 500

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# Ejecutar servidor
if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)
