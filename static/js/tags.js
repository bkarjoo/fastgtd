// Tags module - handles basic tag modal functionality
import { API_BASE, authToken, currentRoot } from './state.js';

// Tag modal state - keep simple for now
let currentTagModalNodeId = null;
let currentNodeTags = [];

// Basic tag modal functions
export function showTagModal() {
    if (!currentRoot) return;
    
    currentTagModalNodeId = currentRoot;
    loadCurrentNodeTags();
    
    document.getElementById('tagModal').classList.remove('hidden');
    document.getElementById('tagSearchInput').focus();
}

export function hideTagModal() {
    document.getElementById('tagModal').classList.add('hidden');
    document.getElementById('tagSearchInput').value = '';
    document.getElementById('tagSuggestions').style.display = 'none';
    currentTagModalNodeId = null;
    currentNodeTags = [];
}

// Load current node's tags
export async function loadCurrentNodeTags() {
    if (!currentTagModalNodeId) return;
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${currentTagModalNodeId}/tags`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            currentNodeTags = await response.json();
            await renderCurrentTags();
        } else {
            currentNodeTags = [];
            await renderCurrentTags();
        }
    } catch (error) {
        console.error('Error loading node tags:', error);
        currentNodeTags = [];
        await renderCurrentTags();
    }
}

// Render current node's tags
async function renderCurrentTags() {
    const container = document.getElementById('currentTagsList');
    
    if (currentNodeTags.length === 0) {
        container.innerHTML = await window.templateSystem.loadAndRender('tags/no-tags-message.html');
        return;
    }
    
    container.innerHTML = currentNodeTags.map(tag => `
        <span class="tag-chip">
            ${escapeHtml(tag.name)}
            <button class="tag-chip-remove" onclick="removeTag('${tag.id}')" title="Remove tag">×</button>
        </span>
    `).join('');
}

// Utility function for HTML escaping
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Placeholder functions for now - will connect to main app later
export function removeTag(tagId) {
    console.log('removeTag called:', tagId);
    // Will implement later
}