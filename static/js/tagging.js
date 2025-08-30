// Tagging module - handles tag creation, search, and application to nodes
import { API_BASE, authToken, currentRoot, currentNodeId, currentNoteId, currentView, nodes, setCurrentRoot } from './state.js';
import { renderTree } from './nodes.js';
import { openNoteView } from './notes.js';
import { renderDetailsPage } from './navigation.js';

// Variables to track tag modal state
let currentTaggingNodeId = null;
let availableTags = [];
let appliedTags = [];

// Show tag modal for a node
export async function showTagModal(nodeId) {
    // Determine which node we're tagging based on context
    if (!nodeId) {
        // Check if we're in note view or note edit mode
        const noteView = document.getElementById('noteView');
        const noteEditor = document.getElementById('noteEditor');
        
        // Try to get currentNoteId from either the imported value or window
        const noteId = currentNoteId || window.currentNoteId;
        
        console.log('Checking for node ID - noteView hidden:', noteView?.classList.contains('hidden'), 
                    'noteEditor hidden:', noteEditor?.classList.contains('hidden'),
                    'currentNoteId (imported):', currentNoteId,
                    'currentNoteId (window):', window.currentNoteId,
                    'noteId (resolved):', noteId,
                    'currentNodeId:', currentNodeId,
                    'currentView:', currentView);
        
        if (noteView && !noteView.classList.contains('hidden') && noteId) {
            nodeId = noteId;
            console.log('Using currentNoteId from note view:', nodeId);
        } else if (noteEditor && !noteEditor.classList.contains('hidden') && noteId) {
            nodeId = noteId;
            console.log('Using currentNoteId from note editor:', nodeId);
        } else if (currentView === 'focus' && currentRoot) {
            nodeId = currentRoot;
            console.log('Using currentRoot from focus view:', nodeId);
        } else if (currentView === 'details' || currentView === 'edit') {
            nodeId = currentNodeId;
            console.log('Using currentNodeId from details/edit view:', nodeId);
        } else {
            console.error('No node ID available for tagging');
            console.error('Debug info:', {
                noteViewHidden: noteView?.classList.contains('hidden'),
                noteEditorHidden: noteEditor?.classList.contains('hidden'),
                currentNoteId_imported: currentNoteId,
                currentNoteId_window: window.currentNoteId,
                currentNodeId,
                currentView,
                currentRoot
            });
            return;
        }
    }
    
    currentTaggingNodeId = nodeId;
    
    // Create modal if it doesn't exist
    let modal = document.getElementById('tagModal');
    if (!modal) {
        createTagModal();
        modal = document.getElementById('tagModal');
    }
    
    // Show the modal
    modal.classList.remove('hidden');
    
    // Load current tags for the node
    await loadNodeTags(nodeId);
    
    // Load all available tags
    await loadAvailableTags();
    
    // Focus on the input
    const input = document.getElementById('tagInput');
    if (input) {
        input.value = '';
        input.focus();
    }
}

// Hide tag modal
export function hideTagModal() {
    const modal = document.getElementById('tagModal');
    if (modal) {
        modal.classList.add('hidden');
    }
    currentTaggingNodeId = null;
}

// Create the tag modal UI
function createTagModal() {
    const modal = document.createElement('div');
    modal.id = 'tagModal';
    modal.className = 'tag-modal hidden';
    modal.innerHTML = `
        <div class="tag-modal-overlay" onclick="hideTagModal()"></div>
        <div class="tag-modal-content">
            <div class="tag-modal-header">
                <h3>Manage Tags</h3>
                <button class="tag-modal-close" onclick="hideTagModal()">×</button>
            </div>
            
            <div class="tag-modal-body">
                <div class="current-tags-section">
                    <h4>Current Tags</h4>
                    <div id="currentTagsList" class="tag-list">
                        <!-- Current tags will be displayed here -->
                    </div>
                </div>
                
                <div class="tag-input-section">
                    <input 
                        type="text" 
                        id="tagInput" 
                        class="tag-input" 
                        placeholder="Type to search or create tags..."
                        oninput="searchForTags(this.value)"
                        onkeydown="handleTagKeydown(event)"
                    />
                    <div id="tagSuggestions" class="tag-suggestions hidden">
                        <!-- Tag suggestions will appear here -->
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add styles
    addTagModalStyles();
    
    document.body.appendChild(modal);
}

// Add CSS styles for the tag modal
function addTagModalStyles() {
    if (document.getElementById('tagModalStyles')) return;
    
    const style = document.createElement('style');
    style.id = 'tagModalStyles';
    style.innerHTML = `
        .tag-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .tag-modal.hidden {
            display: none;
        }
        
        .tag-modal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
        }
        
        .tag-modal-content {
            position: relative;
            background: white;
            border-radius: 12px;
            padding: 20px;
            width: 90%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        }
        
        .tag-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .tag-modal-header h3 {
            margin: 0;
            font-size: 20px;
        }
        
        .tag-modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .current-tags-section {
            margin-bottom: 20px;
        }
        
        .current-tags-section h4 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
        }
        
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            min-height: 32px;
        }
        
        .tag-item {
            background: #007aff;
            color: white;
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 14px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .tag-item .remove-tag {
            cursor: pointer;
            font-weight: bold;
            opacity: 0.8;
        }
        
        .tag-item .remove-tag:hover {
            opacity: 1;
        }
        
        .tag-input-section {
            position: relative;
        }
        
        .tag-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        
        .tag-suggestions {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-top: 4px;
            max-height: 200px;
            overflow-y: auto;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .tag-suggestions.hidden {
            display: none;
        }
        
        .tag-suggestion {
            padding: 10px;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        
        .tag-suggestion:hover {
            background: #f0f0f0;
        }
        
        .tag-suggestion:last-child {
            border-bottom: none;
        }
        
        .tag-suggestion.create-new {
            color: #007aff;
            font-weight: 500;
        }
        
        @media (prefers-color-scheme: dark) {
            .tag-modal-content {
                background: #1c1c1e;
                color: white;
            }
            
            .tag-input {
                background: #2c2c2e;
                border-color: #48484a;
                color: white;
            }
            
            .tag-suggestions {
                background: #2c2c2e;
                border-color: #48484a;
            }
            
            .tag-suggestion:hover {
                background: #3a3a3c;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Load tags currently applied to the node
async function loadNodeTags(nodeId) {
    try {
        const response = await fetch(`${API_BASE}/nodes/${nodeId}/tags`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            appliedTags = await response.json();
            renderCurrentTags();
            
            // Update the node's tags in local state
            if (nodes && nodes[nodeId]) {
                nodes[nodeId].tags = appliedTags;
            }
            
            // If we're in note view, refresh it to show the updated tags
            const noteView = document.getElementById('noteView');
            if (noteView && !noteView.classList.contains('hidden') && currentNoteId === nodeId) {
                openNoteView(nodeId);
            }
            
            // If we're in details view, refresh it to show the updated tags
            if (currentView === 'details' && currentNodeId === nodeId) {
                renderDetailsPage(nodeId);
            }
        }
    } catch (error) {
        console.error('Error loading node tags:', error);
    }
}

// Load all available tags for search
async function loadAvailableTags(query = '') {
    try {
        const url = query 
            ? `${API_BASE}/tags?q=${encodeURIComponent(query)}` 
            : `${API_BASE}/tags`;
            
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            availableTags = await response.json();
        }
    } catch (error) {
        console.error('Error loading available tags:', error);
    }
}

// Render the current tags
function renderCurrentTags() {
    const container = document.getElementById('currentTagsList');
    if (!container) return;
    
    if (appliedTags.length === 0) {
        container.innerHTML = '<span style="color: #999; font-size: 14px;">No tags yet</span>';
        return;
    }
    
    container.innerHTML = appliedTags.map(tag => `
        <span class="tag-item" style="${tag.color ? `background: ${tag.color}` : ''}">
            ${tag.name}
            <span class="remove-tag" onclick="removeTag('${tag.id}')">×</span>
        </span>
    `).join('');
}

// Search tags and show suggestions
export async function searchForTags(query) {
    const suggestionsContainer = document.getElementById('tagSuggestions');
    if (!suggestionsContainer) return;
    
    if (!query || query.trim() === '') {
        suggestionsContainer.classList.add('hidden');
        return;
    }
    
    // Load tags matching the query
    await loadAvailableTags(query);
    
    // Filter out already applied tags
    const appliedTagIds = new Set(appliedTags.map(t => t.id));
    const suggestions = availableTags.filter(tag => !appliedTagIds.has(tag.id));
    
    // Build suggestions HTML
    let html = '';
    
    // Add existing tags
    suggestions.forEach(tag => {
        html += `
            <div class="tag-suggestion" onclick="selectTag('${tag.id}', '${tag.name}')">
                ${tag.name}
            </div>
        `;
    });
    
    // Add "create new" option if query doesn't exactly match any existing tag
    const exactMatch = availableTags.some(tag => 
        tag.name.toLowerCase() === query.toLowerCase()
    );
    
    if (!exactMatch && query.trim()) {
        html += `
            <div class="tag-suggestion create-new" onclick="createAndApplyTag('${query.trim()}')">
                Create new tag: "${query.trim()}"
            </div>
        `;
    }
    
    suggestionsContainer.innerHTML = html;
    suggestionsContainer.classList.remove('hidden');
}

// Select an existing tag
export async function selectTag(tagId, tagName) {
    await applyTagToNode(tagId);
    
    // Clear input and hide suggestions
    const input = document.getElementById('tagInput');
    if (input) {
        input.value = '';
    }
    
    const suggestions = document.getElementById('tagSuggestions');
    if (suggestions) {
        suggestions.classList.add('hidden');
    }
}

// Create a new tag and apply it
export async function createAndApplyTag(tagName) {
    try {
        // First create the tag
        const response = await fetch(`${API_BASE}/tags?name=${encodeURIComponent(tagName)}`, {
            method: 'POST',
            headers: { 
                'Authorization': `Bearer ${authToken}` 
            }
        });
        
        if (response.ok) {
            const newTag = await response.json();
            
            // Apply the tag to the node
            await applyTagToNode(newTag.id);
            
            // Clear input and hide suggestions
            const input = document.getElementById('tagInput');
            if (input) {
                input.value = '';
            }
            
            const suggestions = document.getElementById('tagSuggestions');
            if (suggestions) {
                suggestions.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error creating tag:', error);
    }
}

// Apply a tag to the current node
async function applyTagToNode(tagId) {
    if (!currentTaggingNodeId) return;
    
    try {
        const response = await fetch(
            `${API_BASE}/nodes/${currentTaggingNodeId}/tags/${tagId}`, 
            {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` }
            }
        );
        
        if (response.ok) {
            // Reload the node's tags
            await loadNodeTags(currentTaggingNodeId);
        }
    } catch (error) {
        console.error('Error applying tag:', error);
    }
}

// Remove a tag from the node
export async function removeTag(tagId) {
    if (!currentTaggingNodeId) return;
    
    try {
        const response = await fetch(
            `${API_BASE}/nodes/${currentTaggingNodeId}/tags/${tagId}`, 
            {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${authToken}` }
            }
        );
        
        if (response.ok || response.status === 204) {
            // Reload the node's tags
            await loadNodeTags(currentTaggingNodeId);
        }
    } catch (error) {
        console.error('Error removing tag:', error);
    }
}

// Handle Enter key in tag input
export function handleTagKeydown(event) {
    if (event.key === 'Enter') {
        const input = event.target;
        const query = input.value.trim();
        
        if (query) {
            // Check if there's an exact match in available tags
            const exactMatch = availableTags.find(tag => 
                tag.name.toLowerCase() === query.toLowerCase()
            );
            
            if (exactMatch) {
                selectTag(exactMatch.id, exactMatch.name);
            } else {
                createAndApplyTag(query);
            }
        }
    } else if (event.key === 'Escape') {
        hideTagModal();
    }
}

// Show all tags in a list view (when clicking tag icon at root)
export async function showAllTags() {
    try {
        // Load all tags
        const response = await fetch(`${API_BASE}/tags`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            console.error('Failed to load tags');
            return;
        }
        
        const allTags = await response.json();
        
        // Create a virtual "Tags" view by setting currentRoot to a special value
        setCurrentRoot('__tags__');
        
        // Render the tags list in the tree container
        const container = document.getElementById('nodeTree');
        if (!container) return;
        
        let html = '';
        
        // Add a header
        html += `
            <div class="focus-header">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div onclick="exitTagsView(); event.stopPropagation();" style="cursor: pointer; font-size: 18px; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.1);" title="Back to settings">◀</div>
                        <div style="font-size: 16px; display: flex; align-items: center;">🏷️</div>
                        <div class="focus-title" style="padding: 4px 8px;">All Tags</div>
                    </div>
                    <div style="display: flex; gap: 8px; margin-left: auto;">
                        <button onclick="createNewTag(); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; padding: 4px 12px; background: #007aff; color: white; border: none; border-radius: 6px; font-size: 14px; cursor: pointer;" title="Create new tag">+ New Tag</button>
                    </div>
                </div>
            </div>
        `;
        
        // List all tags
        if (allTags.length === 0) {
            html += '<div style="text-align: center; padding: 20px; color: #666;">No tags yet. Create your first tag!</div>';
        } else {
            html += '<div class="tag-list-container" style="padding: 10px;">';
            allTags.forEach(tag => {
                // Escape the tag ID for use in onclick
                const escapedId = tag.id.replace(/'/g, "\\'");
                html += `
                    <div class="node-item tag-list-item" style="display: flex; align-items: center; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                        <span class="tag-name" style="flex: 1; font-size: 16px;">${tag.name}</span>
                        <span class="tag-description" style="color: #86868b; font-size: 14px; margin-right: 12px;">${tag.description || ''}</span>
                        <button onclick="deleteTag('${escapedId}'); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #ff3b30; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; flex-shrink: 0;" title="Delete tag">×</button>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading tags:', error);
    }
}

// Exit tags view and go back to root
export function exitTagsView() {
    // Go back to settings page
    if (window.showSettings) {
        window.showSettings();
    } else {
        // Fallback to root if showSettings is not available
        setCurrentRoot(null);
        renderTree();
    }
}

// Create a new tag from the tags list view
export async function createNewTag() {
    const tagName = prompt('Enter tag name:');
    if (!tagName || !tagName.trim()) return;
    
    try {
        const response = await fetch(`${API_BASE}/tags?name=${encodeURIComponent(tagName.trim())}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Refresh the tags view
            showAllTags();
        } else {
            alert('Failed to create tag');
        }
    } catch (error) {
        console.error('Error creating tag:', error);
        alert('Error creating tag');
    }
}

// Delete a tag
export async function deleteTag(tagId) {
    if (!confirm('Are you sure you want to delete this tag? It will be removed from all nodes.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/tags/${tagId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok || response.status === 204) {
            // Refresh the tags view
            showAllTags();
        } else {
            alert('Failed to delete tag');
        }
    } catch (error) {
        console.error('Error deleting tag:', error);
        alert('Error deleting tag');
    }
}