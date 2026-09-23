"""Guss: servidor de chat con IA (Flask + OpenRouter).

Variables de entorno:
    OPENROUTER_API_KEY  (obligatoria) Clave de la API de OpenRouter.
    SECRET_KEY          (recomendada) Clave para firmar las cookies de sesión.
    OPENROUTER_MODEL    (opcional)    Modelo a usar. Por defecto "openrouter/free".
    FLASK_DEBUG         (opcional)    "1" para activar el modo debug local.
    LOG_LEVEL           (opcional)    DEBUG, INFO, WARNING... Por defecto INFO.
    DB_PATH             (opcional)    Archivo SQLite del historial. Por defecto "guss.db".

Producción:
    gunicorn "app:create_app()" --workers 2 --threads 4
"""

from __future__ import annotations

import logging
import os
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Iterator

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

# Debe ejecutarse antes de definir Config, que lee os.environ al importarse.
load_dotenv()

logger = logging.getLogger("guss")

Message = dict[str, str]


# ==========================================
# CONFIGURACIÓN
# ==========================================

@dataclass(frozen=True)
class Config:
    """Configuración de la aplicación, leída desde variables de entorno."""

    api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
    api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    model: str = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
    secret_key: str = os.environ.get("SECRET_KEY", "")
    request_timeout: int = 60          # segundos
    max_message_length: int = 4000     # caracteres por mensaje del usuario
    max_history_messages: int = 20     # mensajes enviados como contexto
    db_path: str = os.environ.get("DB_PATH", "guss.db")
    retention_days: int = 30           # días que se conserva una conversación


SYSTEM_PROMPT = """\
Eres Guss, una inteligencia artificial amigable, útil y conversacional.

Respondes principalmente en español.

Tienes memoria de la conversación actual. Debes utilizar el contexto de los \
mensajes anteriores para mantener conversaciones coherentes.

No repitas innecesariamente información que ya conoces.

Si el usuario te cuenta su nombre, preferencias o información durante la \
conversación, puedes utilizarla posteriormente dentro de esta misma conversación.

Sé natural y conversa como una IA moderna.
"""


# ==========================================
# MEMORIA DE CONVERSACIÓN (PERSISTENTE, POR USUARIO)
# ==========================================

class ConversationStore:
    """Historial persistente en SQLite.

    - Sobrevive a reinicios del servidor.
    - Es compartido entre todos los workers de gunicorn.
    - Guarda la conversación completa (para restaurarla en la página), pero
      al modelo solo se le envían los últimos ``max_messages`` mensajes.
    - Las conversaciones más antiguas que ``retention_days`` se borran al arrancar.
    """

    def __init__(self, db_path: str, max_messages: int, retention_days: int) -> None:
        self._path = db_path
        self._max_messages = max_messages
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                """CREATE TABLE IF NOT EXISTS messages (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    cid        TEXT NOT NULL,
                    role       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    created_at REAL NOT NULL)"""
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_messages_cid ON messages (cid, id)")
            db.execute(
                "DELETE FROM messages WHERE created_at < ?",
                (time.time() - retention_days * 86400,),
            )

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._path, timeout=10)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, conversation_id: str, limit: int | None = None) -> list[Message]:
        """Últimos ``limit`` mensajes (por defecto, los que ve el modelo), en orden."""
        with self._db() as db:
            rows = db.execute(
                "SELECT role, content FROM messages WHERE cid = ? ORDER BY id DESC LIMIT ?",
                (conversation_id, limit or self._max_messages),
            ).fetchall()
        return [{"role": role, "content": content} for role, content in reversed(rows)]

    def append(self, conversation_id: str, *messages: Message) -> None:
        now = time.time()
        with self._db() as db:
            db.executemany(
                "INSERT INTO messages (cid, role, content, created_at) VALUES (?, ?, ?, ?)",
                [(conversation_id, m["role"], m["content"], now) for m in messages],
            )

    def clear(self, conversation_id: str) -> None:
        with self._db() as db:
            db.execute("DELETE FROM messages WHERE cid = ?", (conversation_id,))


# ==========================================
# CLIENTE DE OPENROUTER
# ==========================================

class LLMError(Exception):
    """Error al consultar el modelo. El mensaje es seguro para mostrar al usuario."""

    def __init__(self, user_message: str, status_code: int = 502) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.status_code = status_code


class OpenRouterClient:
    """Cliente mínimo para la API de chat completions de OpenRouter."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._http = requests.Session()
        self._http.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })

    def complete(self, messages: list[Message]) -> str:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
        }

        try:
            response = self._http.post(
                self._config.api_url,
                json=payload,
                timeout=self._config.request_timeout,
            )
            response.raise_for_status()
            data = response.json()

        except requests.Timeout as exc:
            logger.warning("Timeout consultando OpenRouter")
            raise LLMError("El modelo tardó demasiado en responder.", 504) from exc

        except requests.HTTPError as exc:
            status = exc.response.status_code
            logger.error("OpenRouter respondió HTTP %s: %s", status, exc.response.text[:500])
            if status == 429:
                raise LLMError("Demasiadas solicitudes. Intenta de nuevo en unos segundos.", 429) from exc
            raise LLMError("El servicio de IA no está disponible en este momento.", 502) from exc

        except (requests.RequestException, ValueError) as exc:
            logger.exception("Error de conexión con OpenRouter")
            raise LLMError("No se pudo conectar con el servicio de IA.", 502) from exc

        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            logger.error("Respuesta inesperada de OpenRouter: %r", data)
            raise LLMError("El modelo devolvió una respuesta inválida.", 502) from exc

        if not text:
            raise LLMError("El modelo devolvió una respuesta vacía.", 502)

        return text


# ==========================================
# FÁBRICA DE LA APLICACIÓN
# ==========================================

def create_app(config: Config | None = None) -> Flask:
    config = config or Config()

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if not config.api_key:
        raise RuntimeError(
            "Falta la variable de entorno OPENROUTER_API_KEY."
        )

    app = Flask(__name__, static_folder="static", static_url_path="/static")

    secret_key = config.secret_key
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning(
            "SECRET_KEY no definida: se generó una temporal. "
            "Las sesiones se perderán al reiniciar el servidor."
        )

    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=not app.debug,   # requiere HTTPS fuera de desarrollo
        MAX_CONTENT_LENGTH=64 * 1024,          # rechaza peticiones > 64 KB
        PERMANENT_SESSION_LIFETIME=timedelta(days=config.retention_days),
    )

    store = ConversationStore(
        db_path=config.db_path,
        max_messages=config.max_history_messages,
        retention_days=config.retention_days,
    )
    llm = OpenRouterClient(config)

    def current_conversation_id() -> str:
        """ID de conversación único por visitante, guardado en su cookie."""
        session.permanent = True   # la cookie sobrevive al cerrar el navegador
        if "cid" not in session:
            session["cid"] = uuid.uuid4().hex
        return session["cid"]

    # ---------- Rutas ----------

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/chat")
    def chat():
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            return jsonify({"error": "No se recibieron datos válidos."}), 400

        mensaje = datos.get("mensaje")
        if not isinstance(mensaje, str) or not mensaje.strip():
            return jsonify({"error": "El mensaje está vacío."}), 400

        mensaje = mensaje.strip()
        if len(mensaje) > config.max_message_length:
            return jsonify({
                "error": f"El mensaje supera los {config.max_message_length} caracteres."
            }), 400

        conversation_id = current_conversation_id()
        mensaje_usuario: Message = {"role": "user", "content": mensaje}

        # El historial solo se modifica si el modelo responde con éxito,
        # así nunca quedan mensajes del usuario sin respuesta.
        contexto = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *store.get(conversation_id),
            mensaje_usuario,
        ]

        try:
            texto_guss = llm.complete(contexto)
        except LLMError as exc:
            return jsonify({"error": exc.user_message}), exc.status_code

        store.append(
            conversation_id,
            mensaje_usuario,
            {"role": "assistant", "content": texto_guss},
        )
        return jsonify({"respuesta": texto_guss})

    @app.get("/history")
    def history():
        """Devuelve la conversación guardada para que la página la restaure."""
        return jsonify({"mensajes": store.get(current_conversation_id(), limit=100)})

    @app.post("/reset")
    def reset():
        """Borra la memoria de la conversación actual."""
        store.clear(current_conversation_id())
        return jsonify({"status": "ok"})

    # ---------- Manejo global de errores ----------

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ruta no encontrada."}), 404

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "La petición es demasiado grande."}), 413

    @app.errorhandler(Exception)
    def unexpected(exc: Exception):
        logger.exception("Error no controlado: %s", exc)
        return jsonify({"error": "Error interno del servidor."}), 500

    return app


# ==========================================
# INICIO LOCAL
# ==========================================

if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG") == "1")
