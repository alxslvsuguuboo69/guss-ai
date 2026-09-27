document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatContainer = document.getElementById("chat-container");
    const sendBtn = document.getElementById("send-btn");

    let conversationHistory = [];

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const messageText = userInput.value.trim();

        if (!messageText) return;

        // Mostrar mensaje del usuario
        appendMessage(messageText, "user");

        conversationHistory.push({
            role: "user",
            content: messageText
        });

        // Limpiar y bloquear controles
        userInput.value = "";
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Crear mensaje vacío del asistente
        const messageDiv = createMessageDiv("assistant");
        const contentDiv = messageDiv.querySelector(".message-content");

        contentDiv.textContent = "Pensando...";

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    messages: conversationHistory
                })
            });

            if (!response.ok) {
                let errorMessage = "Error en la solicitud.";

                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch {
                    // El servidor no devolvió JSON
                }

                contentDiv.textContent = `Error: ${errorMessage}`;
                return;
            }

            if (!response.body) {
                contentDiv.textContent = "El servidor no devolvió un flujo de datos.";
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            let buffer = "";
            let fullText = "";

            contentDiv.textContent = "";

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                buffer += decoder.decode(value, {
                    stream: true
                });

                // Separar eventos SSE completos
                const events = buffer.split("\n\n");

                // El último puede estar incompleto
                buffer = events.pop() || "";

                for (const event of events) {
                    const lines = event.split("\n");

                    for (const line of lines) {
                        if (!line.startsWith("data: ")) {
                            continue;
                        }

                        const jsonStr = line.slice(6).trim();

                        if (!jsonStr) {
                            continue;
                        }

                        // Fin del stream
                        if (jsonStr === "[DONE]") {
                            continue;
                        }

                        try {
                            const parsed = JSON.parse(jsonStr);

                            // Error enviado por nuestro backend
                            if (parsed.error) {
                                contentDiv.textContent = `Error: ${parsed.error}`;
                                continue;
                            }

                            const content =
                                parsed.choices?.[0]?.delta?.content || "";

                            if (!content) {
                                continue;
                            }

                            fullText += content;

                            // Renderizar Markdown en tiempo real
                            if (window.marked) {
                                contentDiv.innerHTML = marked.parse(fullText);
                            } else {
                                contentDiv.textContent = fullText;
                            }

                            scrollToBottom();

                        } catch (error) {
                            console.warn(
                                "No se pudo procesar un evento SSE:",
                                jsonStr
                            );
                        }
                    }
                }
            }

            // Guardar respuesta completa en el historial
            if (fullText) {
                conversationHistory.push({
                    role: "assistant",
                    content: fullText
                });
            }

        } catch (error) {
            console.error("Error:", error);
            contentDiv.textContent =
                "Error de conexión con el servidor.";
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            scrollToBottom();
        }
    });

    function appendMessage(text, sender) {
        const messageDiv = createMessageDiv(sender);
        const contentDiv =
            messageDiv.querySelector(".message-content");

        contentDiv.textContent = text;

        scrollToBottom();

        return messageDiv;
    }

    function createMessageDiv(sender) {
        const messageDiv = document.createElement("div");

        messageDiv.classList.add(
            "message",
            `${sender}-message`
        );

        const contentDiv = document.createElement("div");

        contentDiv.classList.add("message-content");

        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);

        return messageDiv;
    }

    function scrollToBottom() {
        chatContainer.scrollTop =
            chatContainer.scrollHeight;
    }
});
