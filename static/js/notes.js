// Notes module - handles note viewing, editing, and management
import { API_BASE, authToken, nodes, currentNoteId, setCurrentNoteId } from './state.js';
import { renderTree } from './nodes.js';

export function openNoteView(nodeId) {
    const node = nodes[nodeId];
    if (!node || node.node_type !== 'note') return;
    
    setCurrentNoteId(nodeId);
    
    // Update note view content
    document.getElementById('noteViewTitle').textContent = node.title;
    
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