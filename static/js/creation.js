// Creation module - handles creating nodes, folders, tasks, notes, and smart folders
import { API_BASE, authToken, nodes, currentRoot, currentView, currentNodeId, setCurrentRoot } from './state.js';
import { renderTree } from './nodes.js';
import { navigateToFocus } from './navigation.js';

// Helper to refresh smart folders
function refreshAllSmartFolders() {
    if (typeof window.refreshAllSmartFolders === 'function') {
        window.refreshAllSmartFolders();
    } else {
        console.log('Smart folder refresh not available yet');
    }
}

export async function quickCreateFolder() {
    const folderName = prompt('Folder name:');
    if (!folderName || !folderName.trim()) return;
    
    // Determine parent: use currentNodeId if in details/edit view, otherwise currentRoot
    const parentId = (currentView === 'details' || currentView === 'edit') ? currentNodeId : currentRoot;
    
    // Calculate sort order (increment by 10)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), 0);
    
    const nodeData = {
        node_type: 'folder',
        title: folderName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 10
        // No additional data needed for folders
    };
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newFolder = await response.json();
            nodes[newFolder.id] = newFolder;
            
            // If created from details page, navigate to focus on the parent
            if (currentView === 'details' || currentView === 'edit') {
                navigateToFocus(parentId);
            } else {
                renderTree();
            }
            refreshAllSmartFolders();
        } else {
            alert('Failed to create folder');
        }
    } catch (error) {
        console.error('Error creating folder:', error);
        alert('Error creating folder');
    }
}

export async function quickCreateNote() {
    const noteName = prompt('Note title:');
    if (!noteName || !noteName.trim()) return;
    
    // Determine parent: use currentNodeId if in details/edit view, otherwise currentRoot
    const parentId = (currentView === 'details' || currentView === 'edit') ? currentNodeId : currentRoot;
    
    // Calculate sort order (increment by 10)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), 0);
    
    const nodeData = {
        node_type: 'note', 
        title: noteName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 10,
        note_data: {
            body: ' '
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newNote = await response.json();
            nodes[newNote.id] = newNote;
            
            // If created from details page, navigate to focus on the parent
            if (currentView === 'details' || currentView === 'edit') {
                navigateToFocus(parentId);
            } else {
                renderTree();
            }
            refreshAllSmartFolders();
        } else {
            alert('Failed to create note');
        }
    } catch (error) {
        console.error('Error creating note:', error);
        alert('Error creating note');
    }
}

export async function quickCreateTask() {
    const taskName = prompt('Task:');
    if (!taskName || !taskName.trim()) return;
    
    // Determine parent: use currentNodeId if in details/edit view, otherwise currentRoot
    const parentId = (currentView === 'details' || currentView === 'edit') ? currentNodeId : currentRoot;
    
    // Calculate sort order (increment by 10)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), 0);
    
    const nodeData = {
        node_type: 'task',
        title: taskName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 10,
        task_data: {
            status: 'todo',
            priority: 'medium'
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newTask = await response.json();
            nodes[newTask.id] = newTask;
            
            // If created from details page, navigate to focus on the parent
            if (currentView === 'details' || currentView === 'edit') {
                navigateToFocus(parentId);
            } else {
                renderTree();
            }
            refreshAllSmartFolders();
        } else {
            alert('Failed to create task');
        }
    } catch (error) {
        console.error('Error creating task:', error);
        alert('Error creating task');
    }
}

export async function quickCreateSmartFolder() {
    
    const folderName = prompt('Smart folder name:');
    if (!folderName || !folderName.trim()) return;
    
    // Determine parent: use currentNodeId if in details/edit view, otherwise currentRoot
    const parentId = (currentView === 'details' || currentView === 'edit') ? currentNodeId : currentRoot;
    
    // Calculate sort order (increment by 10)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), 0);
    
    const nodeData = {
        node_type: 'smart_folder',
        title: folderName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 10,
        smart_folder_data: {
            rules: null,
            auto_refresh: true,
            description: `Smart folder: ${folderName.trim()}`
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newSmartFolder = await response.json();
            nodes[newSmartFolder.id] = newSmartFolder;
            
            // If created from details page, navigate to focus on the parent
            if (currentView === 'details' || currentView === 'edit') {
                navigateToFocus(parentId);
            } else {
                renderTree();
            }
            refreshAllSmartFolders();
        } else {
            alert('Failed to create smart folder');
        }
    } catch (error) {
        console.error('Error creating smart folder:', error);
        alert('Error creating smart folder');
    }
}

export async function quickCreateTemplate() {
    const templateName = prompt('Template name:');
    if (!templateName || !templateName.trim()) return;
    
    // Calculate sort order (increment by 10)
    const parentId = currentRoot;
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), 0);
    
    const nodeData = {
        node_type: 'template',
        title: templateName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 10,
        template_data: {
            description: '',
            category: 'General',
            usage_count: 0
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newTemplate = await response.json();
            nodes[newTemplate.id] = newTemplate;
            renderTree();
            refreshAllSmartFolders();
        } else {
            const errorText = await response.text();
            console.error('Template creation failed:', response.status, errorText);
            alert(`Failed to create template: ${response.status} - ${errorText}`);
        }
    } catch (error) {
        console.error('Error creating template:', error);
        alert('Error creating template');
    }
}

export async function instantiateTemplate() {
    if (!currentRoot) return;
    
    const template = nodes[currentRoot];
    if (!template || template.node_type !== 'template') return;
    
    // Prompt for the new folder name with a prepopulated suggestion
    const suggestedName = template.title + ' (copy)';
    const newName = prompt('Name for the new folder:', suggestedName);
    if (!newName || !newName.trim()) return;
    
    // Helper function to deep copy nodes
    async function copyNodeRecursively(sourceNode, newParentId, isRoot = false) {
        // Determine the new node type and data
        let nodeData;
        
        if (isRoot) {
            // Convert template to folder (using 'note' type with Container folder body)
            nodeData = {
                node_type: 'note',
                title: newName.trim(),
                parent_id: newParentId,
                sort_order: sourceNode.sort_order || 0,
                note_data: {
                    body: 'Container folder'
                }
            };
        } else {
            // Copy child nodes with their original types
            // Handle invalid node types by converting them to notes
            let nodeType = sourceNode.node_type;
            if (!['task', 'note', 'smart_folder', 'template'].includes(nodeType)) {
                nodeType = 'note';  // Default to note for unknown types
            }
            
            nodeData = {
                node_type: nodeType,
                title: sourceNode.title,
                parent_id: newParentId,
                sort_order: sourceNode.sort_order || 0
            };
            
            // Copy type-specific data
            if (nodeType === 'task' && sourceNode.task_data) {
                nodeData.task_data = { ...sourceNode.task_data };
            } else if (nodeType === 'note') {
                if (sourceNode.note_data) {
                    nodeData.note_data = { ...sourceNode.note_data };
                } else {
                    // If original node didn't have note_data, create it
                    nodeData.note_data = { body: 'Container folder' };
                }
            } else if (nodeType === 'smart_folder' && sourceNode.smart_folder_data) {
                nodeData.smart_folder_data = { ...sourceNode.smart_folder_data };
            } else if (nodeType === 'template' && sourceNode.template_data) {
                nodeData.template_data = { ...sourceNode.template_data };
            }
        }
        
        // Create the node
        try {
            const response = await fetch(`${API_BASE}/nodes/`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}` 
                },
                body: JSON.stringify(nodeData)
            });
            
            if (response.ok) {
                const newNode = await response.json();
                nodes[newNode.id] = newNode;
                
                // Find and copy all children of the source node
                const children = Object.values(nodes).filter(n => n.parent_id === sourceNode.id);
                for (const child of children) {
                    await copyNodeRecursively(child, newNode.id, false);
                }
                
                return newNode;
            } else {
                console.error('Failed to copy node:', await response.text());
                return null;
            }
        } catch (error) {
            console.error('Error copying node:', error);
            return null;
        }
    }
    
    try {
        // Start the deep copy from the template root
        const newFolder = await copyNodeRecursively(template, template.parent_id, true);
        
        if (newFolder) {
            // Navigate to the parent node, or root if no parent
            const parentId = template.parent_id || null;
            setCurrentRoot(parentId);
            
            // Refresh the tree to show the new folder
            renderTree();
            refreshAllSmartFolders();
        } else {
            alert('Failed to instantiate template');
        }
    } catch (error) {
        console.error('Error instantiating template:', error);
        alert('Error instantiating template');
    }
}

// Deprecated - keeping for backward compatibility
export async function useCurrentTemplate() {
    // Redirect to instantiateTemplate
    return instantiateTemplate();
}

export async function createNode(type) {
    const nodeData = {
        node_type: type || 'note'
    };
    
    const titleInput = document.getElementById('newNodeTitle');
    const parentSelect = document.getElementById('newNodeParent');
    
    nodeData.title = titleInput.value.trim();
    nodeData.parent_id = parentSelect.value || null;
    
    if (!nodeData.title) {
        alert('Please enter a title');
        return;
    }
    
    if (type === 'task') {
        nodeData.task_data = {
            status: 'todo',
            priority: 'medium'
        };
    } else if (type === 'note' || !type) {
        nodeData.note_data = {
            body: document.getElementById('nodeType').value === 'folder' ? 'Container folder' : ''
        };
    } else if (type === 'smart_folder') {
        const rules = buildSmartFolderRules ? buildSmartFolderRules() : [];
        nodeData.smart_folder_data = {
            rules: rules.length > 0 ? { conditions: rules, logic: 'all' } : null,
            auto_refresh: true
        };
    }
    
    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(nodeData)
        });
        
        if (response.ok) {
            const newNode = await response.json();
            nodes[newNode.id] = newNode;
            renderTree();
            toggleAddForm();
            titleInput.value = '';
            refreshAllSmartFolders();
        } else {
            const errorData = await response.json();
            alert(`Failed to create node: ${errorData.detail || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error creating node:', error);
        alert('Error creating node');
    }
}

export function toggleAddForm() {
    const form = document.getElementById('addForm');
    if (form) {
        form.classList.toggle('hidden');
        if (!form.classList.contains('hidden')) {
            document.getElementById('newNodeTitle').focus();
            loadParentOptions();
        }
    }
}

export function loadParentOptions() {
    const select = document.getElementById('newNodeParent');
    if (!select) return;
    
    select.innerHTML = '<option value="">Root</option>';
    
    const folders = Object.values(nodes).filter(node => 
        node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder'
    );
    
    folders.forEach(folder => {
        select.innerHTML += `<option value="${folder.id}">${folder.title}</option>`;
    });
    
    if (currentRoot) {
        select.value = currentRoot;
    }
}

export function setAddType(type) {
    const nodeType = document.getElementById('nodeType');
    if (nodeType) {
        nodeType.value = type;
    }
}

// Helper for smart folder rules that will be defined elsewhere
function buildSmartFolderRules() {
    if (typeof window.buildSmartFolderRules === 'function') {
        return window.buildSmartFolderRules();
    }
    return [];
}