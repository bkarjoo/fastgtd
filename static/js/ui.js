// UI module - handles dark mode, settings, navigation, and UI state management
import { currentPage, setCurrentPage, nodes } from './state.js';

export function initDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        document.querySelector('[title="Toggle Dark Mode"]').textContent = '☀️';
    }
}

export function toggleDarkMode() {
    const body = document.body;
    const isDark = body.classList.contains('dark-mode');
    
    if (isDark) {
        body.classList.remove('dark-mode');
        localStorage.setItem('darkMode', 'false');
        document.querySelector('[title="Toggle Dark Mode"]').textContent = '🌙';
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('darkMode', 'true');
        document.querySelector('[title="Toggle Dark Mode"]').textContent = '☀️';
    }
}

export function getNodeIcon(node) {
    if (node.node_type === 'task') {
        if (node.task_data) {
            const status = node.task_data.status;
            if (status === 'done') return '✅';
            if (status === 'in_progress') return '🔄';
            if (status === 'dropped') return '🗑️';
        }
        return '☐';
    } else if (node.node_type === 'node') {
        return '📁';
    } else if (node.node_type === 'note') {
        const isFolder = node.note_data && node.note_data.body === 'Container folder';
        return isFolder ? '📁' : '📝';
    } else if (node.node_type === 'smart_folder') {
        return '💎';
    }
    return '📄';
}

export function backToMain() {
    setCurrentPage('main');
    location.reload();
}

export async function updateNavigation() {
    const navRight = document.getElementById('mainNavRight');
    if (!navRight) return;
    
    if (currentPage === 'settings') {
        navRight.innerHTML = await window.templateSystem.loadAndRender('ui/settings-navigation.html');
    } else {
        navRight.innerHTML = await window.templateSystem.loadAndRender('ui/main-navigation.html');
    }
}