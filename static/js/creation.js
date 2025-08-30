// Creation module - handles quick creation of nodes and form management
import { API_BASE, authToken, nodes, currentRoot, setCurrentRoot, currentNodeId, currentView, addType, setAddType as stateSetAddType } from './state.js';
import { renderTree } from './nodes.js';
import { navigateToFocus } from './navigation.js';

export function toggleAddForm() {
    const addForm = document.getElementById('addForm');
    if (addForm.style.display === 'none' || !addForm.style.display) {
        addForm.style.display = 'block';
        loadParentOptions();
        document.getElementById('nodeTitle').focus();
    } else {
        addForm.style.display = 'none';
    }
}

export async function quickCreateFolder() {
    const folderName = prompt('Folder name:');
    if (!folderName || !folderName.trim()) return;
    
    // Determine parent: use currentNodeId if in details/edit view, otherwise currentRoot
    const parentId = (currentView === 'details' || currentView === 'edit') ? currentNodeId : currentRoot;
    
    const nodeData = {
        node_type: 'node',
        title: folderName.trim(),
        parent_id: parentId || null
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
    
    // Calculate sort order (put at end of siblings)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), -1);
    
    const nodeData = {
        node_type: 'note', 
        title: noteName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 1,
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
    
    const nodeData = {
        node_type: 'task',
        title: taskName.trim(),
        parent_id: parentId || null,
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
    
    // Calculate sort order (put at end of siblings)
    const siblings = Object.values(nodes).filter(n => n.parent_id === parentId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), -1);
    
    const nodeData = {
        node_type: 'smart_folder',
        title: folderName.trim(),
        parent_id: parentId || null,
        sort_order: maxSortOrder + 1,
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
    
    const nodeData = {
        node_type: 'template',
        title: templateName.trim(),
        parent_id: currentRoot || null,
        template_data: {
            template_content: []
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
            alert('Failed to create template');
        }
    } catch (error) {
        console.error('Error creating template:', error);
        alert('Error creating template');
    }
}

export async function useCurrentTemplate() {
    if (!currentRoot) return;
    
    const template = nodes[currentRoot];
    if (!template || template.node_type !== 'template') return;
    
    // For now, just create a copy of the template
    const copyName = template.title + ' (Copy)';
    const nodeData = {
        node_type: 'note',
        title: copyName,
        parent_id: template.parent_id,
        note_data: {
            body: `Template: ${template.title}`
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
            const newNode = await response.json();
            nodes[newNode.id] = newNode;
            setCurrentRoot(template.parent_id);
            renderTree();
            refreshAllSmartFolders();
        } else {
            alert('Failed to use template');
        }
    } catch (error) {
        console.error('Error using template:', error);
        alert('Error using template');
    }
}

export function loadParentOptions() {
    const parentSelect = document.getElementById('parentNodeSelect');
    if (!parentSelect) return;
    
    // Clear existing options
    parentSelect.innerHTML = '';
    
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = currentRoot ? 'Current folder' : 'Root level';
    parentSelect.appendChild(defaultOption);
    
    // Add other folder options
    const folders = Object.values(nodes).filter(node => 
        node.node_type === 'node' ||
        (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder') ||
        node.node_type === 'smart_folder'
    );
    
    folders.forEach(folder => {
        const option = document.createElement('option');
        option.value = folder.id;
        const icon = folder.node_type === 'smart_folder' ? '💎' : '📁';
        option.textContent = `${icon} ${folder.title}`;
        parentSelect.appendChild(option);
    });
}

export function setAddType(type) {
    stateSetAddType(type);
    
    // Update UI to reflect the selected type
    const buttons = document.querySelectorAll('.add-type-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
    
    // Show/hide type-specific sections
    const taskSection = document.getElementById('taskSection');
    if (taskSection) {
        taskSection.style.display = type === 'task' ? 'block' : 'none';
    }
}

// These functions are defined in mobile-app.js and will be extracted in later steps
function refreshAllSmartFolders() { if (typeof window.refreshAllSmartFolders === 'function') window.refreshAllSmartFolders(); }