/**
 * NutriScan AI — Assistant Chatbot Module
 * Sends contextual nutrition queries to Gemini AI and renders chat stream.
 */

const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const btnChatSend = document.getElementById("btn-chat-send");
const btnClearChat = document.getElementById("btn-clear-chat");

function scrollToBottom() {
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function appendMessage(role, text) {
    if (!chatMessages) return;

    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${role === 'user' ? 'message-user' : 'message-assistant'}`;

    if (role === 'assistant') {
        const header = document.createElement("div");
        header.style.fontSize = "0.8rem";
        header.style.color = "var(--primary-light)";
        header.style.fontWeight = "700";
        header.style.marginBottom = "0.25rem";
        header.textContent = "🥗 NutriScan AI Assistant";
        bubble.appendChild(header);
    }

    const content = document.createElement("div");
    // Convert newlines to breaks safely
    content.innerHTML = text.replace(/\n/g, "<br>");
    bubble.appendChild(content);

    chatMessages.appendChild(bubble);
    scrollToBottom();
}

function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.id = "typing-indicator";
    indicator.className = "message-bubble message-assistant";
    indicator.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--text-muted); font-size: 0.88rem;">
            <span>🥗 Gemini AI is thinking</span>
            <span style="animation: pulse 1s infinite;">...</span>
        </div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
}

function removeTypingIndicator() {
    const ind = document.getElementById("typing-indicator");
    if (ind) ind.remove();
}

async function sendMessage(text) {
    const msg = (text || chatInput.value).trim();
    if (!msg) return;

    // Clear input
    if (chatInput) chatInput.value = "";

    // Show user message
    appendMessage("user", msg);

    // Show typing
    showTypingIndicator();
    if (btnChatSend) btnChatSend.disabled = true;

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg })
        });

        removeTypingIndicator();
        if (btnChatSend) btnChatSend.disabled = false;

        const data = await resp.json();
        if (data.success) {
            appendMessage("assistant", data.reply);
        } else {
            appendMessage("assistant", "⚠️ " + (data.message || "Failed to get response from AI."));
        }
    } catch (err) {
        removeTypingIndicator();
        if (btnChatSend) btnChatSend.disabled = false;
        appendMessage("assistant", "⚠️ Network error: " + err.message);
    }
}

function sendPrompt(promptText) {
    if (chatInput) chatInput.value = promptText;
    sendMessage(promptText);
}

// Event Listeners
if (btnChatSend) {
    btnChatSend.addEventListener("click", () => sendMessage());
}

if (chatInput) {
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

if (btnClearChat) {
    btnClearChat.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear your conversation history?")) return;
        try {
            const resp = await fetch("/api/chat/history", { method: "DELETE" });
            const data = await resp.json();
            if (data.success) {
                chatMessages.innerHTML = `
                    <div class="message-bubble message-assistant">
                        <div style="font-size: 0.8rem; color: var(--primary-light); font-weight: 700; margin-bottom: 0.25rem;">
                            🥗 NutriScan AI Assistant
                        </div>
                        <div>Conversation history cleared. How can I help you today?</div>
                    </div>
                `;
            }
        } catch (err) {
            alert("Error clearing chat: " + err.message);
        }
    });
}

// Scroll to bottom on initial load
scrollToBottom();
