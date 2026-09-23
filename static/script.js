```javascript
console.log("GUSS AI: JavaScript cargado correctamente");

document.addEventListener("DOMContentLoaded", () => {

    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const loadingIndicator = document.getElementById("loading");

    console.log("Elementos encontrados:", {
        chatBox: !!chatBox,
        userInput: !!userInput,
        sendBtn: !!sendBtn,
        loading: !!loadingIndicator
    });

    if (!chatBox || !userInput || !sendBtn || !loadingIndicator) {
        console.error("GUSS AI: No se encontraron los elementos del chat.");
        return;
    }

    async function sendMessage() {

        const message = userInput.value.trim();

        if (!message) {
            return;
        }

        console.log("Enviando mensaje:", message);

        addMessage(message, "user");

        userInput.value = "";
        sendBtn.disabled = true;
        loadingIndicator.style.display = "block";

        try {

            console.log("Conectando con /chat...");

            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mensaje: message
                })
            });

            console.log("Respuesta del servidor:", response.status);

            const data = await response.json();

            console.log("Datos recibidos:", data);

            if (response.ok) {

                addMessage(
                    data.respuesta || "Guss no devolvió ninguna respuesta.",
                    "guss"
                );

            } else {

                addMessage(
                    "Error del servidor: " + (data.error || "Error desconocido"),
                    "guss"
                );

                console.error("Error del servidor:", data);

            }

        } catch (error) {

            console.error("Error de conexión:", error);

            addMessage(
                "No pude conectarme con Guss. Revisa la consola.",
                "guss"
            );

        } finally {

            loadingIndicator.style.display = "none";
            sendBtn.disabled = false;
            userInput.focus();

        }
    }

    function addMessage(text, sender) {

        const messageDiv = document.createElement("div");

        messageDiv.classList.add("message");

        if (sender === "user") {
            messageDiv.classList.add("user-message");
        } else {
            messageDiv.classList.add("guss-message");
        }

        messageDiv.textContent = text;

        chatBox.appendChild(messageDiv);

        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendBtn.addEventListener("click", () => {
        console.log("Botón Enviar presionado");
        sendMessage();
    });

    userInput.addEventListener("keydown", (event) => {

        if (event.key === "Enter") {
            event.preventDefault();
            console.log("Enter presionado");
            sendMessage();
        }

    });

    console.log("GUSS AI: Chat inicializado correctamente");
});
```
