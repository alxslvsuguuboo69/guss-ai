```javascript
console.log("🔥 GUSS AI: SCRIPT CARGADO 🔥");

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const loadingIndicator = document.getElementById("loading");

console.log("Elementos encontrados:", {
    chatBox,
    userInput,
    sendBtn,
    loadingIndicator
});

sendBtn.addEventListener("click", function () {
    console.log("🔥 BOTÓN ENVIAR FUNCIONA 🔥");
});

userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        console.log("🔥 ENTER FUNCIONA 🔥");
    }
});
```
