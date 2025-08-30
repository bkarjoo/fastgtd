// Chat/AI module - handles floating chat widget and AI interactions
import { API_BASE, authToken, currentRoot } from './state.js';
import { logout } from './auth.js';

// Chat state
let chatHistory = [];
let isLoading = false;

// Toggle floating chat widget
export function toggleFloatingChat() {
    const chat = document.getElementById('floatingChat');
    chat.classList.toggle('active');
    
    if (chat.classList.contains('active')) {
        // Focus the input when opening chat
        setTimeout(() => {
            document.getElementById('chatInput').focus();
        }, 100);
    }
}

// Close floating chat widget
export function closeFloatingChat() {
    document.getElementById('floatingChat').classList.remove('active');
}

// Send chat message
export function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    // Add user message to chat
    addChatMessage(message, true);
    input.value = '';
    
    // Add to history
    chatHistory.push({ role: 'user', content: message });
    
    // Send to API
    sendToAI(message);
}

// Add message to chat display
function addChatMessage(text, isUser = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${isUser ? 'user' : 'ai'}`;
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add loading message
function addLoadingMessage() {
    const messagesContainer = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-loading';
    loadingDiv.id = 'chatLoading';
    loadingDiv.textContent = 'AI is thinking...';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Remove loading message
function removeLoadingMessage() {
    const loading = document.getElementById('chatLoading');
    if (loading) loading.remove();
}

// Update AI context with current node
export async function updateAIContext() {
    if (!currentRoot || !authToken) return;
    try {
        await fetch(`${API_BASE}/ai/set-context`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ current_node_id: currentRoot })
        });
    } catch (e) {
        console.log('AI context update failed (non-critical):', e.message);
    }
}

// Send message to AI and handle response
export async function sendToAI(message) {
    isLoading = true;
    document.getElementById('chatSendBtn').disabled = true;
    addLoadingMessage();

    try {
        const res = await fetch(`${API_BASE}/ai/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ message, history: chatHistory })
        });

        removeLoadingMessage();

        if (res.status === 401) {
            // Auth expired; force re-login
            try { logout(); } catch {}
        }
        if (!res.ok) {
            const errText = await res.text().catch(() => '');
            throw new Error(errText || `HTTP ${res.status}`);
        }

        // Supports ChatResponse {response} or StepResponse {final_response}
        const data = await res.json();
        const aiText = data.response || data.final_response || 'No response.';

        addChatMessage(aiText);
        chatHistory.push({ role: 'assistant', content: aiText });
        
        // Refresh the tree only if AI took actions (like adding tasks)
        if (data.actions_taken) {
            await loadNodes();
        }
    } catch (e) {
        removeLoadingMessage();
        // Fallback temporary message if AI endpoint is unavailable
        const fallback = "🔧 The AI assistant is currently unavailable.\n\nYou can:\n• Create tasks and notes using the interface\n• Organize them in folders\n• Use smart folders to filter content\n• Tag items for better organization\n\nRetry in a bit.";
        addChatMessage(fallback);
        chatHistory.push({ role: 'assistant', content: fallback });
    } finally {
        isLoading = false;
        document.getElementById('chatSendBtn').disabled = false;
    }
}

// Handle chat input key press
export function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

// Functions that will be extracted in later steps
function loadNodes() { if (typeof window.loadNodes === 'function') window.loadNodes(); }