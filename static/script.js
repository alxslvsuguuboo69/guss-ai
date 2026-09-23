console.log("GUSS AI: JavaScript cargado correctamente");

document.addEventListener("DOMContentLoaded", function () {

    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const loadingIndicator = document.getElementById("loading");

    console.log("Chat encontrado:", !!chatBox);
    console.log("Input encontrado:", !!userInput);
    console.log("Botón encontrado:", !!sendBtn);

    async function sendMessage() {

        const message = userInput.value.trim();

        if (!message) return;

        console.log("Enviando:", message);

        chatBox.innerHTML += `
            <div class="message user-message">
                ${message}
            </div>
        `;

        userInput.value = "";
        loadingIndicator.style.display = "block";

        try {

            console.log("Llamando a /chat...");

            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    mensaje: message
                })
            });

            console.log("Estado:", response.status);

            const data = await response.json();

            console.log("Respuesta:", data);

            if (response.ok) {

                chatBox.innerHTML += `
                    <div class="message guss-message">
                        ${data.respuesta}
                    </div>
                `;

            } else {

                chatBox.innerHTML += `
                    <div class="message guss-message">
                        Error: ${data.error}
                    </div>
                `;
            }

        } catch (error) {

            console.error("ERROR:", error);

            chatBox.innerHTML += `
                <div class="message guss-message">
                    Error de conexión con el servidor.
                </div>
            `;

        } finally {

            loadingIndicator.style.display = "none";
        }
    }

    sendBtn.addEventListener("click", sendMessage);

    userInput.addEventListener("keydown", function (event) {

        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }

    });

});
