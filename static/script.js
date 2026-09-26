const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const messagesDiv = document.getElementById("messages");

function addMessage(role, content) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.textContent = content;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage("user", message);
    input.value = "";
    input.disabled = true;
    form.querySelector("button").disabled = true;

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "Error del servidor");
        }

        addMessage("assistant", data.reply);
    } catch (err) {
        addMessage("assistant", `Error: ${err.message}`);
    } finally {
        input.disabled = false;
        form.querySelector("button").disabled = false;
        input.focus();
    }
});
