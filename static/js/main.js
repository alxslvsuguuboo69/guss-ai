document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatContainer = document.getElementById("chat-container");
    const sendBtn = document.getElementById("send-btn");

    // Historial en memoria de la sesión actual
    let conversationHistory = [];

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // Mostrar mensaje del usuario
        appendMessage(messageText, "user");
        conversationHistory.push({ role: "user", content: messageText });

        userInput.value = "";
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Mostrar indicador temporal
        const loadingDiv = appendMessage("Pensando...", "assistant");

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: conversationHistory })
            });

            const data = await response.json();

            if (response.ok) {
                loadingDiv.querySelector(".message-content").textContent = data.response;
                conversationHistory.push({ role: "assistant", content: data.response });
            } else {
                loadingDiv.querySelector(".message-content").textContent = `Error: ${data.error}`;
            }
        } catch (error) {
            loadingDiv.querySelector(".message-content").textContent = "Error de conexión con el servidor.";
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    });

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        contentDiv.textContent = text;

        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        scrollToBottom();

        return messageDiv;
    }

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
