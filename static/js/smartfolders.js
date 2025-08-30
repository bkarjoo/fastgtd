// Smart Folders module - handles smart folder content loading and management
import { API_BASE, authToken, nodes, currentRoot } from './state.js';
import { renderTree } from './nodes.js';

// Smart folder loading state
let loadingSmartFolderContents = new Set();

// Basic smart folder content loading
export async function loadSmartFolderContents(smartFolderId, level) {
    // For now, just add a placeholder - will implement async rendering later
    // This would fetch from the smart folder contents API endpoint
}

export async function refreshSmartFolderContents(smartFolderId) {
    console.log('Refreshing smart folder contents for:', smartFolderId); // Debug log
    try {
        const response = await fetch(`${API_BASE}/nodes/${smartFolderId}/contents`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const smartFolderContents = await response.json();
            console.log('Refreshed smart folder contents:', smartFolderContents); // Debug log
            
            // Remove old smart folder children from nodes
            Object.keys(nodes).forEach(nodeId => {
                if (nodes[nodeId]._smartFolderChild === smartFolderId) {
                    delete nodes[nodeId];
                }
            });
            
            // Add refreshed nodes to the global nodes object with smart folder marker
            smartFolderContents.forEach(node => {
                node._smartFolderChild = smartFolderId; // Mark as smart folder child
                nodes[node.id] = node;
            });
            
            console.log('Smart folder contents refreshed successfully'); // Debug log
        } else {
            console.error('Failed to refresh smart folder contents:', response.status);
        }
    } catch (error) {
        console.error('Error refreshing smart folder contents:', error);
    }
}

export async function refreshAllSmartFolders() {
    console.log('Refreshing all smart folders due to data change'); // Debug log
    
    // Find all smart folders that are currently loaded (have children in memory)
    const loadedSmartFolders = new Set();
    Object.values(nodes).forEach(node => {
        if (node._smartFolderChild) {
            loadedSmartFolders.add(node._smartFolderChild);
        }
    });
    
    // Refresh each loaded smart folder
    for (const smartFolderId of loadedSmartFolders) {
        await refreshSmartFolderContents(smartFolderId);
    }
    
    // If we're currently focused on a smart folder, re-render to show updated results
    const currentNode = nodes[currentRoot];
    if (currentNode && currentNode.node_type === 'smart_folder') {
        renderTree();
    }
}

export async function loadSmartFolderContentsFocus(smartFolderId) {
    // Prevent recursive calls
    if (loadingSmartFolderContents.has(smartFolderId)) {
        return;
    }
    
    loadingSmartFolderContents.add(smartFolderId);
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${smartFolderId}/contents`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const smartFolderContents = await response.json();
            
            // Clear old smart folder children before adding new ones (for refresh)
            Object.keys(nodes).forEach(nodeId => {
                if (nodes[nodeId]._smartFolderChild === smartFolderId) {
                    delete nodes[nodeId];
                }
            });
            
            // Add refreshed nodes to the global nodes object with special marker
            smartFolderContents.forEach(node => {
                node._smartFolderChild = smartFolderId; // Mark as smart folder child
                nodes[node.id] = node;
            });
            
            // Re-render the tree to show the loaded contents
            renderTree();
        } else {
            console.error('Failed to load smart folder contents');
        }
    } catch (error) {
        console.error('Error loading smart folder contents:', error);
    } finally {
        loadingSmartFolderContents.delete(smartFolderId);
    }
}