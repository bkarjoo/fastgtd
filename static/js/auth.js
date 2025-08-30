// Authentication module - handles login/logout and screen transitions
import { API_BASE, setAuthToken, clearState } from './state.js';

export function showMainApp() {
    document.getElementById('loginScreen').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
}

export function showLoginScreen() {
    document.getElementById('loginScreen').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

export async function login() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageEl = document.getElementById('authMessage');
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            setAuthToken(data.access_token);
            
            messageEl.innerHTML = await window.templateSystem.loadAndRender('auth/success-message.html', {
                message: 'Logged in!'
            });
            setTimeout(() => {
                showMainApp();
                // Call loadNodes if available (will be imported by mobile-app.js)
                if (typeof window.loadNodes === 'function') {
                    window.loadNodes();
                }
            }, 500);
        } else {
            const error = await response.json();
            messageEl.innerHTML = await window.templateSystem.loadAndRender('auth/error-message.html', {
                message: error.detail
            });
        }
    } catch (error) {
        messageEl.innerHTML = await window.templateSystem.loadAndRender('auth/error-message.html', {
            message: error.message
        });
    }
}

export function logout() {
    clearState();
    showLoginScreen();
}