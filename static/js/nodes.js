// Node operations module - handles node loading, rendering, navigation, and CRUD operations
import { API_BASE, authToken, nodes, setNodes, expandedNodes, currentRoot, setCurrentRoot, currentPage, buildNodeURL } from './state.js';
import { logout } from './auth.js';
import { getNodeIcon, updateNavigation } from './ui.js';
import { navigateToFocus, navigateToDetails } from './navigation.js';

export async function loadNodes(parentId = null) {
    try {
        const url = buildNodeURL(`${API_BASE}/nodes/`, parentId);
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const nodeList = await response.json();
            setNodes({});
            nodeList.forEach(node => nodes[node.id] = node);
            updateHeaderButtons();
            renderTree();
            
            // Load tags for smart folder creation
            loadAllTags();
        } else if (response.status === 401) {
            logout();
        } else {
            document.getElementById('nodeTree').innerHTML = 
                '<div style="text-align: center; padding: 40px 20px; color: #ff3b30;">Failed to load nodes</div>';
        }
    } catch (error) {
        document.getElementById('nodeTree').innerHTML = 
            `<div style="text-align: center; padding: 40px 20px; color: #ff3b30;">Error: ${error.message}</div>`;
    }
}

export function refreshNodes() {
    loadNodes();
}

export async function loadAllTags() {
    try {
        const response = await fetch(`${API_BASE}/tags/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            window.allTags = await response.json();
        }
    } catch (error) {
        console.error('Failed to load tags:', error);
    }
}

export function renderTree() {
    const container = document.getElementById('nodeTree');
    
    // Add global click listener to detect ANY clicks
    if (!window.globalClickListenerAdded) {
        window.globalClickListenerAdded = true;
    }
    
    let html = '';
    
    // Show current node info when in focus mode
    if (currentRoot) {
        const currentNode = nodes[currentRoot];
        if (currentNode) {
            // Get appropriate icon/checkbox for current node
            let iconHtml;
            const isTask = currentNode.node_type === 'task';
            const isCompleted = isTask && currentNode.task_data.status === 'done';
            
            // Prioritize node type over whether it has children
            if (isTask) {
                // For tasks in focus, show toggle-able checkbox like in list view
                iconHtml = `<input type="checkbox" class="task-checkbox" ${isCompleted ? 'checked' : ''} 
                           onclick="toggleTaskComplete('${currentNode.id}')" onchange="event.stopPropagation()" 
                           style="transform: scale(1.2); margin: 0;">`;
            } else if (currentNode.node_type === 'smart_folder') {
                // Smart folder
                const isExpanded = expandedNodes.has(currentNode.id);
                iconHtml = isExpanded ? '▽' : '▽';
            } else if (currentNode.node_type === 'template') {
                // Template - show package icon
                iconHtml = '📦';
            } else {
                // For non-tasks, check if it's a folder or regular note
                const isFolder = (currentNode.node_type === 'node') || 
                                (currentNode.node_type === 'note' && currentNode.note_data && currentNode.note_data.body === 'Container folder');
                
                if (isFolder) {
                    const isExpanded = expandedNodes.has(currentNode.id);
                    iconHtml = isExpanded ? '📂' : '📁';
                } else {
                    // Regular note (not a container folder)
                    iconHtml = '📝';
                }
            }
            
            html += `
                <div class="focus-header" data-node-id="${currentNode.parent_id || 'root'}" ondragover="handleDragOver(event)" ondrop="handleDropOut(event)">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div onclick="exitFocusMode(); event.stopPropagation();" style="cursor: pointer; font-size: 18px; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.1);" title="Exit focus mode">◀</div>
                            <div style="font-size: 16px; display: flex; align-items: center;">${iconHtml}</div>
                            <div class="focus-title" onclick="handleFocusTitleClick(); event.stopPropagation();" style="cursor: pointer; padding: 4px 8px; border-radius: 4px; transition: background 0.2s;" onmouseover="this.style.background='rgba(0,0,0,0.05)'" onmouseout="this.style.background='transparent'" title="${currentNode.node_type === 'note' && currentNode.note_data && currentNode.note_data.body !== 'Container folder' ? 'Click to view note content' : currentNode.node_type === 'smart_folder' ? 'Click to view rules' : 'Click to view details'}">${escapeHtml(currentNode.title)}</div>
                        </div>
                        <button onclick="deleteCurrentNode(); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #ff3b30; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-left: auto;" title="Delete this ${currentNode.node_type}">×</button>
                    </div>
                </div>
            `;
        }
    }

    // Find and show root-level nodes or children of current focus
    const parentId = currentRoot || null;
    const rootNodes = Object.values(nodes).filter(node => node.parent_id === parentId);
    
    // Sort by created_at (newest first)
    rootNodes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    if (rootNodes.length === 0) {
        if (currentRoot) {
            html += '<div style="text-align: center; padding: 20px; color: #666;">This folder is empty</div>';
        } else {
            html += '<div style="text-align: center; padding: 20px; color: #666;">No nodes yet. Create your first one!</div>';
        }
    } else {
        html += '<ul class="node-list">';
        rootNodes.forEach(node => {
            html += renderNodeItem(node, 0);
        });
        html += '</ul>';
    }

    container.innerHTML = html;
}

function renderNodeItem(node, level) {
    const children = Object.values(nodes).filter(child => child.parent_id === node.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedNodes.has(node.id);
    const indent = level * 20;
    
    let html = '';
    
    // Skip smart folder item rendering if we're inside the smart folder
    if (node.node_type === 'smart_folder' && currentRoot === node.id) {
        return html;
    }
    
    let iconHtml;
    const isTask = node.node_type === 'task';
    
    if (isTask) {
        const isCompleted = node.task_data && node.task_data.status === 'done';
        const isInProgress = node.task_data && node.task_data.status === 'in_progress';
        const isDropped = node.task_data && node.task_data.status === 'dropped';
        
        if (isCompleted) {
            iconHtml = `<input type="checkbox" class="task-checkbox" checked 
                       onclick="toggleTaskComplete('${node.id}')" onchange="event.stopPropagation()">`;
        } else if (isInProgress) {
            iconHtml = `<input type="checkbox" class="task-checkbox task-in-progress" 
                       onclick="toggleTaskComplete('${node.id}')" onchange="event.stopPropagation()">`;
        } else if (isDropped) {
            iconHtml = `<input type="checkbox" class="task-checkbox task-dropped" 
                       onclick="toggleTaskComplete('${node.id}')" onchange="event.stopPropagation()">`;
        } else {
            iconHtml = `<input type="checkbox" class="task-checkbox" 
                       onclick="toggleTaskComplete('${node.id}')" onchange="event.stopPropagation()">`;
        }
    } else if (node.node_type === 'smart_folder') {
        iconHtml = `<span class="folder-icon" onclick="handleFolderIconClick('${node.id}'); event.stopPropagation();" style="cursor: pointer; user-select: none;">💎</span>`;
    } else if (node.node_type === 'template') {
        iconHtml = `<span class="folder-icon" onclick="handleFolderIconClick('${node.id}'); event.stopPropagation();" style="cursor: pointer; user-select: none;">📦</span>`;
    } else {
        const isFolder = (node.node_type === 'node') || 
                        (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder');
        
        if (isFolder || hasChildren) {
            const folderIcon = isExpanded ? '📂' : '📁';
            iconHtml = `<span class="folder-icon" onclick="handleFolderIconClick('${node.id}'); event.stopPropagation();" style="cursor: pointer; user-select: none;">${folderIcon}</span>`;
        } else {
            iconHtml = `<span style="user-select: none;">📝</span>`;
        }
    }

    const nodeClasses = ['node-item'];
    if (isTask && node.task_data) {
        if (node.task_data.status === 'done') nodeClasses.push('completed');
        if (node.task_data.status === 'in_progress') nodeClasses.push('in-progress');
        if (node.task_data.status === 'dropped') nodeClasses.push('dropped');
        if (node.task_data.priority === 'high') nodeClasses.push('high-priority');
        if (node.task_data.priority === 'medium') nodeClasses.push('medium-priority');
    }

    const dragAttributes = `draggable="true" ondragstart="handleDragStart(event)" ondragend="handleDragEnd(event)"`;
    const dropAttributes = `ondragover="handleDragOver(event)" ondrop="handleDrop(event)"`;

    // Add expand triangle for folders/parents
    let expandHtml = '';
    if (hasChildren) {
        const expandIcon = isExpanded ? '▽' : '▶';
        expandHtml = `<div class="node-expand" onclick="toggleExpand('${node.id}'); event.stopPropagation();">${expandIcon}</div>`;
    } else {
        expandHtml = `<div class="node-expand"></div>`; // Empty space for alignment
    }

    html += `
        <li class="${nodeClasses.join(' ')}" data-node-id="${node.id}" ${dragAttributes} ${dropAttributes} style="margin-left: ${indent}px;" onclick="handleNodeClick('${node.id}', ${!hasChildren && !isTask})">
            ${expandHtml}
            <div class="node-icon">${iconHtml}</div>
            <div class="node-content">
                <div class="node-title">${escapeHtml(node.title)}</div>
            </div>
        </li>
    `;

    if (hasChildren && isExpanded && node.node_type !== 'smart_folder') {
        children.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        children.forEach(child => {
            html += renderNodeItem(child, level + 1);
        });
    }

    return html;
}

export function toggleExpand(nodeId) {
    if (expandedNodes.has(nodeId)) {
        expandedNodes.delete(nodeId);
    } else {
        expandedNodes.add(nodeId);
    }
    renderTree();
}

export function handleNodeClick(nodeId, isList) {
    console.log('you clicked me');
    const node = nodes[nodeId];
    if (!node) return;

    if (node.node_type === 'note' && node.note_data && node.note_data.body !== 'Container folder') {
        // Real notes should always open note view when clicked
        openNoteView(nodeId);
    } else if (node.node_type === 'smart_folder') {
        setCurrentRoot(nodeId);
        loadSmartFolderContentsFocus(nodeId);
    } else if (node.node_type === 'template') {
        useCurrentTemplate();
    } else {
        const childCount = Object.values(nodes).filter(n => n.parent_id === nodeId).length;
        
        if (childCount === 0) {
            // No children - go to details page
            navigateToDetails(nodeId);
        } else {
            // Has children - set as current root and render tree
            setCurrentRoot(nodeId);
            renderTree();
        }
    }
}

export function handleFolderIconClick(nodeId) {
    const node = nodes[nodeId];
    if (!node) return;

    if (node.node_type === 'smart_folder') {
        if (expandedNodes.has(nodeId)) {
            expandedNodes.delete(nodeId);
        } else {
            expandedNodes.add(nodeId);
            loadSmartFolderContents(nodeId, 0);
        }
    } else if (node.node_type === 'template') {
        setCurrentRoot(nodeId);
        renderTree();
    } else {
        toggleExpand(nodeId);
    }
}

export function exitFocusMode() {
    if (!currentRoot) return;
    
    const currentNode = nodes[currentRoot];
    if (currentNode) {
        // Go to parent, or root if no parent
        const parentId = currentNode.parent_id || null;
        setCurrentRoot(parentId);
    } else {
        // Fallback to root if current node not found
        setCurrentRoot(null);
    }
    
    renderTree();
}

export async function toggleTaskComplete(nodeId) {
    const node = nodes[nodeId];
    if (!node || node.node_type !== 'task') return;

    const currentStatus = node.task_data?.status || 'todo';
    let newStatus;
    
    switch (currentStatus) {
        case 'todo':
            newStatus = 'done';
            break;
        case 'done':
            newStatus = 'todo';
            break;
        case 'in_progress':
            newStatus = 'done';
            break;
        case 'dropped':
            newStatus = 'todo';
            break;
        default:
            newStatus = 'done';
    }

    try {
        const response = await fetch(`${API_BASE}/nodes/${nodeId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ...node,
                task_data: { ...node.task_data, status: newStatus }
            })
        });

        if (response.ok) {
            const updatedNode = await response.json();
            nodes[nodeId] = updatedNode;
            renderTree();
            refreshAllSmartFolders();
        }
    } catch (error) {
        console.error('Failed to update task:', error);
    }
}

export async function createNode() {
    const title = document.getElementById('nodeTitle').value;
    if (!title.trim()) return;

    const parentSelect = document.getElementById('parentNodeSelect');
    const parentId = parentSelect && parentSelect.value ? parentSelect.value : (currentRoot || null);
    
    const nodeData = {
        title: title.trim(),
        node_type: window.addType || 'task',
        parent_id: parentId
    };

    if (window.addType === 'task') {
        const priority = document.getElementById('taskPriority')?.value || 'medium';
        const status = document.getElementById('taskStatus')?.value || 'todo';
        nodeData.task_data = { priority, status };
    } else if (window.addType === 'note') {
        nodeData.note_data = { body: '' };
    } else if (window.addType === 'smart_folder') {
        const conditions = buildSmartFolderRules();
        nodeData.smart_folder_data = { conditions };
    }

    try {
        const response = await fetch(`${API_BASE}/nodes/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(nodeData)
        });

        if (response.ok) {
            const newNode = await response.json();
            nodes[newNode.id] = newNode;
            
            document.getElementById('nodeTitle').value = '';
            toggleAddForm();
            renderTree();
            refreshAllSmartFolders();
        } else {
            alert('Failed to create node');
        }
    } catch (error) {
        console.error('Failed to create node:', error);
        alert('Failed to create node');
    }
}

export async function deleteCurrentNode() {
    if (!currentRoot) {
        alert('No node selected to delete');
        return;
    }
    
    const node = nodes[currentRoot];
    if (!node) return;
    
    const nodeTypeText = node.node_type === 'smart_folder' ? 'smart folder' : node.node_type;
    if (!confirm(`Are you sure you want to delete this ${nodeTypeText}? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/nodes/${currentRoot}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const parentId = node.parent_id;
            delete nodes[currentRoot];
            
            setCurrentRoot(parentId);
            renderTree();
            refreshAllSmartFolders();
        } else {
            alert('Failed to delete node');
        }
    } catch (error) {
        console.error('Failed to delete node:', error);
        alert('Failed to delete node');
    }
}

export async function editFocusedNodeTitle() {
    if (!currentRoot) return;
    
    const node = nodes[currentRoot];
    if (!node) return;
    
    const newTitle = prompt('Enter new title:', node.title);
    if (newTitle && newTitle.trim() && newTitle.trim() !== node.title) {
        try {
            const response = await fetch(`${API_BASE}/nodes/${currentRoot}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...node,
                    title: newTitle.trim()
                })
            });

            if (response.ok) {
                const updatedNode = await response.json();
                nodes[currentRoot] = updatedNode;
                renderTree();
                refreshAllSmartFolders();
            }
        } catch (error) {
            console.error('Failed to update title:', error);
        }
    }
}

export function handleFocusTitleClick() {
    console.log('[handleFocusTitleClick] Called from nodes.js line 305');
    const node = nodes[currentRoot];
    if (!node) return;
    
    // Use new navigation system to go to details page
    if (window.navigateToDetails) {
        window.navigateToDetails(currentRoot);
    } else {
        // Fallback to existing behavior
        if (node.node_type === 'note' && node.note_data && node.note_data.body !== 'Container folder') {
            openNoteView(currentRoot);
        } else if (node.node_type === 'smart_folder') {
            openSmartFolderRulesView(currentRoot);
        } else {
            editFocusedNodeTitle();
        }
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateHeaderButtons() {
    // Use the new modular updateNavigation function
    updateNavigation();
}

// These functions are defined in mobile-app.js and will be extracted in later steps
function openNoteView(nodeId) { if (typeof window.openNoteView === 'function') window.openNoteView(nodeId); }
function loadSmartFolderContentsFocus(smartFolderId) { if (typeof window.loadSmartFolderContentsFocus === 'function') window.loadSmartFolderContentsFocus(smartFolderId); }
function loadSmartFolderContents(smartFolderId, level) { if (typeof window.loadSmartFolderContents === 'function') window.loadSmartFolderContents(smartFolderId, level); }
function useCurrentTemplate() { if (typeof window.useCurrentTemplate === 'function') window.useCurrentTemplate(); }
function buildSmartFolderRules() { if (typeof window.buildSmartFolderRules === 'function') return window.buildSmartFolderRules(); return []; }
function refreshAllSmartFolders() { if (typeof window.refreshAllSmartFolders === 'function') window.refreshAllSmartFolders(); }
function toggleAddForm() { if (typeof window.toggleAddForm === 'function') window.toggleAddForm(); }
function openSmartFolderRulesView(nodeId) { if (typeof window.openSmartFolderRulesView === 'function') window.openSmartFolderRulesView(nodeId); }