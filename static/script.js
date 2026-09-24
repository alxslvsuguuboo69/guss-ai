"use strict";

(() => {
    const chatBox = document.getElementById("chat-box");
    const input = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const newChatBtn = document.getElementById("new-chat-btn");

    // Cinco estrellas; el CSS (.star-1 ... .star-5) posiciona y anima cada una.
    const STARS_HTML = ["✦", "✧", "✦", "✧", "✦"]
        .map((s, i) => `<span class="star star-${i + 1}">${s}</span>`)
        .join("");

    let busy = false;

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addMessage(text, classes) {
        const el = document.createElement("div");
        el.className = `message ${classes}`;
        el.textContent = text; // textContent evita inyección de HTML (XSS)
        chatBox.appendChild(el);
        scrollToBottom();
    }

    /** Burbuja de Guss con estrellas animadas dentro del chat. */
    function showThinking() {
        const el = document.createElement("div");
        el.className = "message guss-message thinking-message";
        el.setAttribute("role", "status");
        el.innerHTML =
            `<span class="stars-loader" aria-hidden="true">${STARS_HTML}</span>` +
            `<span class="loading-text">Guss está pensando...</span>`;
        chatBox.appendChild(el);
        scrollToBottom();
        return el;
    }

    async function api(url, options = {}) {
        let res;
        try {
            res = await fetch(url, {
                headers: { "Content-Type": "application/json" },
                ...options,
            });
        } catch {
            throw new Error("No se pudo conectar con el servidor.");
        }
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
        return data;
    }

    function autosize() {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
    }

    async function send() {
        const text = input.value.trim();
        if (!text || busy) return;

        busy = true;
        sendBtn.disabled = true;
        addMessage(text, "user-message");
        input.value = "";
        autosize();

        const thinking = showThinking();

        try {
            const data = await api("/chat", {
                method: "POST",
                body: JSON.stringify({ mensaje: text }),
            });
            thinking.remove();
            addMessage(data.respuesta, "guss-message");
        } catch (err) {
            thinking.remove();
            addMessage(err.message, "guss-message error-message");
        } finally {
            busy = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async function loadHistory() {
        try {
            const { mensajes } = await api("/history");
            mensajes.forEach((m) =>
                addMessage(m.content, m.role === "user" ? "user-message" : "guss-message")
            );
        } catch {
            /* sin historial: se queda solo el saludo */
        }
    }

    async function newChat() {
        if (busy || !confirm("¿Borrar la conversación y empezar de nuevo?")) return;
        try {
            await api("/reset", { method: "POST" });
            while (chatBox.children.length > 1) chatBox.lastChild.remove(); // deja el saludo
        } catch (err) {
            addMessage(err.message, "guss-message error-message");
        }
    }

    sendBtn.addEventListener("click", send);
    newChatBtn.addEventListener("click", newChat);
    input.addEventListener("input", autosize);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
            e.preventDefault();
            send();
        }
    });

    loadHistory();
    input.focus();
})();
