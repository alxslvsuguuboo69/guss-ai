import os
import urllib.request
import urllib.error
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# 1. SEGURIDAD: La clave ya no está escrita aquí. 
# Render la inyectará de forma segura.
API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELO = "openrouter/free" # O el modelo específico que prefieras

# 2. ENDPOINT: En vez de un bucle while, creamos una "ruta" web
@app.route("/chat", methods=["POST"])
def chat():
    # En vez de input(), recibimos los datos que envía la página web
    datos_web = request.json
    mensaje = datos_web.get("mensaje", "")

    if not mensaje:
        return jsonify({"error": "El mensaje está vacío"}), 400

    # 3. TU LÓGICA ORIGINAL (Conservada intacta)
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

        peticion.add_header("Authorization", f"Bearer {API_KEY}")
        peticion.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(peticion) as respuesta:
            resultado = json.loads(respuesta.read().decode("utf-8"))

        texto_guss = resultado["choices"][0]["message"]["content"]

        # 4. En vez de print(), devolvemos la respuesta a la página web en formato JSON
        return jsonify({"respuesta": texto_guss})

    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8")
        return jsonify({"error": f"Error HTTP {e.code}: {cuerpo}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Esto es necesario para que Render sepa cómo iniciar tu app
if __name__ == "__main__":
    app.run(debug=True)
    app.run(debug=True)
