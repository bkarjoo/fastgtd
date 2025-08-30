// Notes module - handles note viewing, editing, and management
import { API_BASE, authToken, nodes, currentNoteId, setCurrentNoteId } from './state.js';
import { renderTree } from './nodes.js';

export function openNoteView(nodeId) {
    const node = nodes[nodeId];
    if (!node || node.node_type !== 'note') return;
    
    setCurrentNoteId(nodeId);
    // Also set it on window for compatibility
    window.currentNoteId = nodeId;
    
    // Update note view content
    document.getElementById('noteViewTitle').textContent = node.title;
    
    // Add tags display between header and content
    const noteContent = document.getElementById('noteViewContent');
    const noteHeader = document.querySelector('#noteView .note-header');
    
    // Remove existing tags section if present
    const existingTags = document.querySelector('#noteView .node-tags-section');
    if (existingTags) {
        existingTags.remove();
    }
    
    // Create tags section
    const tagsSection = document.createElement('div');
    tagsSection.className = 'node-tags-section';
    tagsSection.style.cssText = 'padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; background: #f8f9fa; border-bottom: 1px solid #e0e0e0; min-height: 48px;';
    
    // Add tags if they exist
    if (node.tags && node.tags.length > 0) {
        node.tags.forEach(tag => {
            const tagBubble = document.createElement('span');
            tagBubble.className = 'tag-bubble';
            tagBubble.style.cssText = 'display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: #007AFF; color: white; border-radius: 12px; font-size: 12px; font-weight: 500;';
            tagBubble.innerHTML = `
                ${tag.name}
                <button onclick="removeTagFromNoteView('${nodeId}', '${tag.id}')" style="background: none; border: none; color: white; cursor: pointer; padding: 0; margin: 0; font-size: 16px; line-height: 1; display: flex; align-items: center; justify-content: center; width: 16px; height: 16px; opacity: 0.8;">×</button>
            `;
            tagsSection.appendChild(tagBubble);
        });
    } else {
        const noTags = document.createElement('span');
        noTags.style.cssText = 'color: #999; font-size: 12px; font-style: italic;';
        noTags.textContent = 'No tags';
        tagsSection.appendChild(noTags);
    }
    
    // Insert tags section before the content (after header)
    if (noteContent && noteContent.parentNode) {
        noteContent.parentNode.insertBefore(tagsSection, noteContent);
    }
    
    // Render markdown content
    const markdownContent = (node.note_data && node.note_data.body) || '';
    const htmlContent = marked.parse(markdownContent);
    document.getElementById('noteViewContent').innerHTML = htmlContent;
    
    // Show note view
    document.getElementById('noteView').classList.remove('hidden');
    document.getElementById('mainApp').classList.add('hidden');
}

export function closeNoteView() {
    document.getElementById('noteView').classList.add('hidden');
    document.getElementById('mainApp').classList.remove('hidden');
    setCurrentNoteId(null);
    // Also clear it on window for compatibility
    window.currentNoteId = null;
}

export function editNote() {
    if (!currentNoteId) return;
    
    const node = nodes[currentNoteId];
    if (!node) return;
    
    // Populate editor with current content
    document.getElementById('noteEditorTitle').value = node.title;
    document.getElementById('noteEditorBody').value = (node.note_data && node.note_data.body) || '';
    
    // Show editor
    document.getElementById('noteEditor').classList.remove('hidden');
    document.getElementById('noteView').classList.add('hidden');
    
    // Focus on body for immediate editing
    setTimeout(() => {
        document.getElementById('noteEditorBody').focus();
    }, 100);
}

export async function deleteNoteFromView() {
    if (!currentNoteId) return;
    
    const node = nodes[currentNoteId];
    if (!node) return;
    
    const confirmMessage = `Are you sure you want to delete "${node.title}"?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${currentNoteId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Remove from local nodes
            delete nodes[currentNoteId];
            
            // Close note view and return to tree
            closeNoteView();
            
            // Refresh the tree
            renderTree();
        } else {
            alert('Failed to delete note');
        }
    } catch (error) {
        console.error('Error deleting note:', error);
        alert('Error deleting note');
    }
}

export function cancelNoteEdit() {
    // Go back to note view
    document.getElementById('noteEditor').classList.add('hidden');
    document.getElementById('noteView').classList.remove('hidden');
}

export async function saveNote() {
    if (!currentNoteId) return;
    
    const node = nodes[currentNoteId];
    if (!node) return;
    
    const newTitle = document.getElementById('noteEditorTitle').value.trim();
    const newBody = document.getElementById('noteEditorBody').value.trim();
    
    if (!newTitle) {
        alert('Note title cannot be empty');
        return;
    }
    
    if (!newBody) {
        alert('Note content cannot be empty');
        return;
    }
    
    try {
        // Build payload
        const payload = {
            title: newTitle,
            node_type: 'note',
            parent_id: node.parent_id,
            sort_order: node.sort_order,
            note_data: {
                body: newBody
            }
        };
        
        const response = await fetch(`${API_BASE}/nodes/${currentNoteId}`, {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            // Update local state
            node.title = newTitle;
            if (node.note_data) {
                node.note_data.body = newBody;
            }
            
            // Update note view with new content
            document.getElementById('noteViewTitle').textContent = newTitle;
            const htmlContent = marked.parse(newBody);
            document.getElementById('noteViewContent').innerHTML = htmlContent;
            
            // Go back to note view
            document.getElementById('noteEditor').classList.add('hidden');
            document.getElementById('noteView').classList.remove('hidden');
            
            // Update tree if needed
            renderTree();
            
            // Refresh smart folders since note content was updated
            refreshAllSmartFolders();
        } else {
            alert('Failed to save note');
        }
    } catch (error) {
        console.error('Error saving note:', error);
        alert('Error saving note');
    }
}

// These functions are defined in mobile-app.js and will be extracted in later steps
function refreshAllSmartFolders() { if (typeof window.refreshAllSmartFolders === 'function') window.refreshAllSmartFolders(); }

// Function to remove a tag from a note
async function removeTagFromNoteView(nodeId, tagId) {
    if (!confirm('Remove this tag?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${nodeId}/tags/${tagId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Update local node data
            if (nodes[nodeId] && nodes[nodeId].tags) {
                nodes[nodeId].tags = nodes[nodeId].tags.filter(tag => tag.id !== tagId);
            }
            
            // Re-render the note view to show updated tags
            openNoteView(nodeId);
        } else {
            alert('Failed to remove tag');
        }
    } catch (error) {
        console.error('Error removing tag:', error);
        alert('Error removing tag');
    }
}

// Make it globally available
window.removeTagFromNoteView = removeTagFromNoteView;