// Settings module - handles settings page functionality and default node management
import { API_BASE, authToken, nodes, setCurrentPage } from './state.js';
import { updateNavigation, getNodeIcon } from './ui.js';

export async function showSettings() {
    setCurrentPage('settings');
    updateNavigation();
    
    // Find and clear the tree container completely
    const treeContainer = document.getElementById('nodeTree');
    if (treeContainer) {
        // Clear template cache for settings view to ensure latest version
        window.templateSystem.cache.delete('settings/settings-view.html');
        treeContainer.innerHTML = await window.templateSystem.loadAndRender('settings/settings-view.html', {
            defaultNodeText: 'Not set'
        });
        
        // Load current default for display
        loadCurrentDefaultForDisplay();
    }
}

export async function editSettings() {
    const treeContainer = document.getElementById('nodeTree');
    if (treeContainer) {
        treeContainer.innerHTML = await window.templateSystem.loadAndRender('settings/settings-editor.html');
        
        // Populate the dropdown with available nodes
        populateDefaultNodeSelect();
    }
}

export async function populateDefaultNodeSelect() {
    const select = document.getElementById('defaultNodeSelect');
    if (!select || !nodes) return;
    
    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add only root-level nodes (nodes with no parent) as options
    const rootNodes = Object.values(nodes).filter(node => !node.parent_id);
    
    rootNodes.forEach(node => {
        const option = document.createElement('option');
        option.value = node.id;
        const icon = getNodeIcon(node);
        option.textContent = `${icon} ${node.title}`;
        select.appendChild(option);
    });
    
    // Load and set current default
    await loadCurrentDefault();
}

export async function loadCurrentDefault() {
    try {
        const response = await fetch(`${API_BASE}/settings/default-node`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('defaultNodeSelect');
            if (select && data.node_id) {
                select.value = data.node_id;
            }
        }
    } catch (error) {
        console.error('Failed to load current default:', error);
    }
}

export async function saveSettings() {
    const select = document.getElementById('defaultNodeSelect');
    const nodeId = select?.value;
    
    try {
        const response = await fetch(`${API_BASE}/settings/default-node`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ node_id: nodeId || null })
        });
        
        if (response.ok) {
            // Go back to settings view
            showSettings();
        } else {
            alert('Failed to save settings');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        alert('Failed to save settings');
    }
}

export async function loadCurrentDefaultForDisplay() {
    try {
        const response = await fetch(`${API_BASE}/settings/default-node`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const textSpan = document.getElementById('currentDefaultText');
            if (textSpan && data.node_id && nodes[data.node_id]) {
                const node = nodes[data.node_id];
                const icon = getNodeIcon(node);
                textSpan.textContent = `${icon} ${node.title}`;
            } else if (textSpan) {
                textSpan.textContent = 'Not set';
            }
        }
    } catch (error) {
        console.error('Failed to load current default for display:', error);
        // Don't show error to user, just leave as "Not set"
    }
}