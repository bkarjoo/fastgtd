// Navigation module for 3-page flow implementation
import { 
    currentView, 
    currentNodeId, 
    navigationStack,
    nodes,
    currentRoot,
    authToken,
    API_BASE,
    setCurrentView, 
    setCurrentNodeId, 
    pushNavigationState, 
    popNavigationState,
    clearNavigationStack,
    setCurrentRoot
} from './state.js';
import { renderTree } from './nodes.js';
// Functions will be available via window from main.js global bindings

/**
 * Navigation system for 3-page flow:
 * 1. Focus Page - Main content view (existing focus mode)
 * 2. Detail Render Page - Read-only details view
 * 3. Detail Edit Page - Editable details view
 */

// Show/hide page containers
function showPage(pageId) {
    // Hide all page containers
    const pages = ['mainApp', 'nodeDetails', 'nodeEdit'];
    pages.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.classList.add('hidden');
        }
    });
    
    // Show requested page
    const targetPage = document.getElementById(pageId);
    if (targetPage) {
        targetPage.classList.remove('hidden');
    } else {
        console.error(`Target page ${pageId} not found!`);
    }
}

// Navigate to Focus Page (existing main view)
export function navigateToFocus(nodeId = null) {
    pushNavigationState({
        view: currentView,
        nodeId: currentNodeId,
        timestamp: Date.now()
    });
    
    setCurrentView('focus');
    setCurrentNodeId(null);
    showPage('mainApp');
    
    // If nodeId provided, focus on that node
    if (nodeId && nodes[nodeId]) {
        // Use existing focus mode functionality
        setCurrentRoot(nodeId);
        renderTree();
    }
}

// Navigate to Detail Render Page (read-only)
export function navigateToDetails(nodeId) {
    if (!nodeId || !nodes[nodeId]) {
        console.error('Invalid node ID for details view:', nodeId);
        return;
    }
    
    pushNavigationState({
        view: currentView,
        nodeId: currentNodeId,
        timestamp: Date.now()
    });
    
    setCurrentView('details');
    setCurrentNodeId(nodeId);
    
    renderDetailsPage(nodeId);
    showPage('nodeDetails');
}

// Navigate to Detail Edit Page (editable)
export function navigateToEdit(nodeId) {
    if (!nodeId || !nodes[nodeId]) {
        console.error('Invalid node ID for edit view:', nodeId);
        return;
    }
    
    pushNavigationState({
        view: currentView,
        nodeId: currentNodeId,
        timestamp: Date.now()
    });
    
    setCurrentView('edit');
    setCurrentNodeId(nodeId);
    
    renderEditPage(nodeId);
    showPage('nodeEdit');
}

// Navigate back to previous page
export function navigateBack() {
    // Simple approach: always go back to focus page when navigating back
    // This provides predictable navigation behavior
    console.log('Navigating back from', currentView);
    navigateToFocus();
}

// Delete node from details page
export async function deleteNodeFromDetails() {
    if (!currentNodeId || !nodes[currentNodeId]) {
        console.error('No valid node to delete');
        return;
    }
    
    const node = nodes[currentNodeId];
    const confirmMessage = `Are you sure you want to delete "${node.title}"?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${currentNodeId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Remove from local nodes
            delete nodes[currentNodeId];
            
            // Navigate back to focus view
            navigateToFocus();
            
            // Refresh the tree to show the updated node list
            renderTree();
        } else {
            alert('Failed to delete node');
        }
    } catch (error) {
        console.error('Error deleting node:', error);
        alert('Error deleting node');
    }
}

// Check for unsaved changes before navigation
export function navigateWithUnsavedCheck(navigateFunction, ...args) {
    if (currentView === 'edit' && hasUnsavedChanges()) {
        if (!confirm('You have unsaved changes. Are you sure you want to leave this page?')) {
            return;
        }
    }
    navigateFunction(...args);
}

// Render the Details Page (read-only)
export function renderDetailsPage(nodeId) {
    const node = nodes[nodeId];
    if (!node) return;
    
    // Create details page container if it doesn't exist
    if (!document.getElementById('nodeDetails')) {
        createDetailsPageContainer();
    }
    
    const container = document.getElementById('nodeDetails');
    const contentArea = container.querySelector('#nodeDetailsContent');
    
    // Update header
    const titleElement = container.querySelector('#nodeDetailsTitle');
    const editButton = container.querySelector('.edit-button');
    if (titleElement) {
        titleElement.textContent = node.title;
    }
    if (editButton) {
        editButton.setAttribute('onclick', `navigateToEdit('${nodeId}')`);
    }
    
    // Add tags display for folders, tasks, and notes
    const pageHeader = container.querySelector('.page-header');
    if (pageHeader && (node.node_type === 'folder' || node.node_type === 'task' || node.node_type === 'note' || node.node_type === 'node')) {
        // Check if tags section already exists and remove it
        const existingTags = container.querySelector('.node-tags-section');
        if (existingTags) {
            existingTags.remove();
        }
        
        // Create tags section
        const tagsSection = document.createElement('div');
        tagsSection.className = 'node-tags-section';
        
        // Add tags if they exist
        if (node.tags && node.tags.length > 0) {
            node.tags.forEach(tag => {
                const tagBubble = document.createElement('span');
                tagBubble.className = 'tag-bubble';
                tagBubble.innerHTML = `
                    ${tag.name}
                    <button class="tag-remove-btn" onclick="removeTagFromNode('${nodeId}', '${tag.id}')">×</button>
                `;
                tagsSection.appendChild(tagBubble);
            });
        } else {
            const noTags = document.createElement('span');
            noTags.className = 'no-tags-text';
            noTags.textContent = 'No tags';
            tagsSection.appendChild(noTags);
        }
        
        // Insert tags section after the page header
        pageHeader.insertAdjacentElement('afterend', tagsSection);
    }
    
    // Update navigation buttons based on node type
    const navRight = container.querySelector('.nav-right');
    if (navRight && node.node_type === 'task') {
        // For tasks, remove smart folder and template buttons, add tag
        navRight.innerHTML = `
            <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
            <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
            <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
            <button onclick="quickCreateNote()" title="Create Note">📝</button>
            <button onclick="quickCreateTask()" title="Create Task">✅</button>
            <button onclick="showTagModal()" title="Manage Tags">🏷️</button>
            <button onclick="logout()" title="Logout">🚪</button>
        `;
    } else if (navRight && node.node_type === 'template') {
        // For templates, remove smart folder and template buttons, no tag
        navRight.innerHTML = `
            <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
            <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
            <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
            <button onclick="quickCreateNote()" title="Create Note">📝</button>
            <button onclick="quickCreateTask()" title="Create Task">✅</button>
            <button onclick="logout()" title="Logout">🚪</button>
        `;
    } else if (navRight && node.node_type === 'smart_folder') {
        // For smart folders, only show template button
        navRight.innerHTML = `
            <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
            <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
            <button onclick="quickCreateTemplate()" title="Create Template">📦</button>
            <button onclick="logout()" title="Logout">🚪</button>
        `;
    } else if (navRight) {
        // For folders and notes, show all buttons including tag
        navRight.innerHTML = `
            <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
            <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
            <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
            <button onclick="quickCreateNote()" title="Create Note">📝</button>
            <button onclick="quickCreateTask()" title="Create Task">✅</button>
            <button onclick="quickCreateSmartFolder()" title="Create Smart Folder">💎</button>
            <button onclick="quickCreateTemplate()" title="Create Template">📦</button>
            <button onclick="showTagModal()" title="Manage Tags">🏷️</button>
            <button onclick="logout()" title="Logout">🚪</button>
        `;
    }
    
    // Render content based on node type
    contentArea.innerHTML = renderNodeDetailsContent(node);
}

// Render the Edit Page (editable)
function renderEditPage(nodeId) {
    const node = nodes[nodeId];
    if (!node) return;
    
    // Aggressively remove ALL potential duplicate elements
    const existingEdits = document.querySelectorAll('.node-page');
    existingEdits.forEach(el => {
        if (el.id === 'nodeEdit' || el.querySelector('#taskStatus')) {
            el.remove();
        }
    });
    
    // Also remove any orphaned form elements
    const orphanedStatus = document.querySelectorAll('#taskStatus');
    const orphanedPriority = document.querySelectorAll('#taskPriority');
    orphanedStatus.forEach(el => el.remove());
    orphanedPriority.forEach(el => el.remove());
    
    // Create fresh edit page container
    createEditPageContainer();
    
    const container = document.getElementById('nodeEdit');
    const contentArea = container.querySelector('#nodeEditContent');
    
    // Update header
    const titleInput = container.querySelector('#nodeEditTitle');
    if (titleInput) {
        titleInput.value = node.title;
    }
    
    // Update navigation based on node type
    const navRight = container.querySelector('.nav-right');
    if (navRight) {
        if (node.node_type === 'task' || node.node_type === 'note' || node.node_type === 'folder' ||
            (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder')) {
            // For tasks, notes, and folders - add tag icon
            navRight.innerHTML = `
                <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                <button onclick="showTagModal()" title="Manage Tags">🏷️</button>
                <button onclick="logout()" title="Logout">🚪</button>
            `;
        } else {
            // For other node types (templates, smart folders), no tag icon
            navRight.innerHTML = `
                <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                <button onclick="logout()" title="Logout">🚪</button>
            `;
        }
    }
    
    // Render form based on node type
    contentArea.innerHTML = renderNodeEditForm(node);
    
    // Set dropdown selections to current values (only once when page loads)
    if (node.node_type === 'task') {
        setTimeout(() => {
            const taskData = node.task_data || {};
            const statusSelect = document.getElementById('taskStatus');
            const prioritySelect = document.getElementById('taskPriority');
            
            if (statusSelect) {
                // Handle both string values and enum objects
                let statusValue = taskData.status;
                if (typeof statusValue === 'object' && statusValue && statusValue.value) {
                    statusValue = statusValue.value; // Handle enum objects
                }
                const targetValue = statusValue || 'todo';
                statusSelect.value = targetValue;
                console.log('Initial status set to:', statusSelect.value, 'from', taskData.status);
            }
            
            if (prioritySelect) {
                // Handle both string values and enum objects  
                let priorityValue = taskData.priority;
                if (typeof priorityValue === 'object' && priorityValue && priorityValue.value) {
                    priorityValue = priorityValue.value; // Handle enum objects
                }
                const targetValue = priorityValue || 'medium';
                prioritySelect.value = targetValue;
                console.log('Initial priority set to:', prioritySelect.value, 'from', taskData.priority);
            }
        }, 0);
    }
}

// Create Details Page Container
function createDetailsPageContainer() {
    const container = document.createElement('div');
    container.id = 'nodeDetails';
    container.className = 'node-page hidden';
    container.innerHTML = `
        <header class="top-nav">
            <div class="nav-right">
                <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
                <button onclick="quickCreateNote()" title="Create Note">📝</button>
                <button onclick="quickCreateTask()" title="Create Task">✅</button>
                <button onclick="quickCreateSmartFolder()" title="Create Smart Folder">💎</button>
                <button onclick="quickCreateTemplate()" title="Create Template">📦</button>
                <button onclick="logout()" title="Logout">🚪</button>
            </div>
        </header>
        
        <div class="page-header">
            <button class="back-button" onclick="navigateBack()">◀</button>
            <h1 id="nodeDetailsTitle" class="page-title">Node Details</h1>
            <button onclick="deleteNodeFromDetails(); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #ff3b30; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer;" title="Delete this node">×</button>
            <button class="edit-button" onclick="navigateToEdit(currentNodeId)">✎</button>
        </div>
        
        <div class="page-content" id="nodeDetailsContent">
            Loading...
        </div>
    `;
    document.body.appendChild(container);
}

// Create Edit Page Container
function createEditPageContainer() {
    const container = document.createElement('div');
    container.id = 'nodeEdit';
    container.className = 'node-page hidden';
    container.innerHTML = `
        <header class="top-nav">
            <div class="nav-right">
                <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                <button onclick="logout()" title="Logout">🚪</button>
            </div>
        </header>
        
        <div class="page-header">
            <button class="back-button" onclick="navigateBack()">◀</button>
            <input type="text" id="nodeEditTitle" class="title-input" placeholder="Node title">
            <button class="save-button" onclick="saveNodeChanges()">✓</button>
        </div>
        
        <div class="page-content" id="nodeEditContent">
            Loading...
        </div>
    `;
    document.body.appendChild(container);
}

// Get display-friendly node type
function getDisplayNodeType(node) {
    if (node.node_type === 'folder' || node.node_type === 'node' || 
        (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder')) {
        return 'Folder';
    }
    
    switch (node.node_type) {
        case 'node': return 'Folder';
        case 'folder': return 'Folder';
        case 'task': return 'Task';
        case 'note': return 'Note';
        case 'smart_folder': return 'Smart Folder';
        case 'template': return 'Template';
        default: return node.node_type.charAt(0).toUpperCase() + node.node_type.slice(1);
    }
}

// Render node-specific details content
function renderNodeDetailsContent(node) {
    const nodeType = node.node_type;
    let html = `<div class="node-metadata">`;
    
    // Check if this is a folder (either pure node or legacy container)
    const isFolder = (node.node_type === 'node') || 
                    (node.node_type === 'folder') ||
                    (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder');
    
    // For tasks, render task details first (without Basic Information)
    if (nodeType === 'task') {
        html += renderTaskDetails(node);
    } else {
        // For non-tasks, show Basic Information first
        html += `
            <div class="metadata-section">
                <h3>Basic Information</h3>
                <div class="metadata-item">
                    <label>Type:</label>
                    <span>${getDisplayNodeType(node)}</span>
                </div>
                <div class="metadata-item">
                    <label>Created:</label>
                    <span>${new Date(node.created_at).toLocaleString()}</span>
                </div>
                <div class="metadata-item">
                    <label>Updated:</label>
                    <span>${new Date(node.updated_at).toLocaleString()}</span>
                </div>
            </div>
        `;
        
        if (isFolder) {
            html += renderGenericNodeDetails(node);
        } else {
            // Node-specific content for non-folders
            switch (nodeType) {
                case 'note':
                    html += renderNoteDetails(node);
                    break;
                case 'smart_folder':
                    html += renderSmartFolderDetails(node);
                    break;
                case 'template':
                    html += renderTemplateDetails(node);
                    break;
                default:
                    html += renderGenericNodeDetails(node);
            }
        }
    }
    
    html += `</div>`;
    return html;
}

// Render node-specific edit forms
function renderNodeEditForm(node) {
    let html = `<form class="node-edit-form">`;
    
    // Check if this is a folder (either pure node or legacy container)
    const isFolder = (node.node_type === 'node') || 
                    (node.node_type === 'folder') ||
                    (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder');
    
    if (isFolder) {
        html += renderGenericNodeEditForm(node);
    } else {
        // Node-specific edit forms for non-folders
        switch (node.node_type) {
            case 'task':
                html += renderTaskEditForm(node);
                break;
            case 'note':
                html += renderNoteEditForm(node);
                break;
            case 'smart_folder':
                html += renderSmartFolderEditForm(node);
                break;
            case 'template':
                html += renderTemplateEditForm(node);
                break;
            default:
                html += renderGenericNodeEditForm(node);
        }
    }
    
    html += `</form>`;
    return html;
}

// Node-specific detail renderers (to be implemented)
function renderTaskDetails(node) {
    const taskData = node.task_data || {};
    let html = '';
    
    // Show description prominently at the top without a label
    html += `
        <div style="font-size: 1em; line-height: 1.4; padding: 12px; background: rgba(0,0,0,0.02); border-radius: 8px; margin-bottom: 20px; text-align: left !important; display: block; white-space: normal; margin: 0 0 20px 0;">
            ${taskData.description || '<em style="color: #999;">No description provided</em>'}
        </div>`;
    
    // Important task metadata
    html += `
        <div class="metadata-section">
            <h3>Task Status</h3>
            <div class="metadata-item">
                <label>Status:</label>
                <span class="task-status-${taskData.status}" style="font-weight: 600; padding: 2px 8px; border-radius: 4px;">${taskData.status || 'todo'}</span>
            </div>
            <div class="metadata-item">
                <label>Priority:</label>
                <span class="task-priority-${taskData.priority}" style="font-weight: 600; padding: 2px 8px; border-radius: 4px;">${taskData.priority || 'medium'}</span>
            </div>`;
    
    // Dates section
    html += `
            <div class="metadata-item">
                <label>Due Date:</label>
                <span>${taskData.due_at ? new Date(taskData.due_at).toLocaleString() : 'Not set'}</span>
            </div>
            <div class="metadata-item">
                <label>Start Date:</label>
                <span>${taskData.earliest_start_at ? new Date(taskData.earliest_start_at).toLocaleString() : 'Not set'}</span>
            </div>`;
    
    // Organization metadata (less prominent)
    html += `
        </div>
        <div class="metadata-section">
            <h3>Organization</h3>
            <div class="metadata-item">
                <label>Parent:</label>
                <span>${node.parent_id ? (nodes[node.parent_id]?.title || 'Unknown') : 'Root level'}</span>
            </div>
            <div class="metadata-item">
                <label>Sort Order:</label>
                <span>${node.sort_order || 0}</span>
            </div>`;
    
    if (taskData.completed_at) {
        html += `
            <div class="metadata-item">
                <label>Completed:</label>
                <span>${new Date(taskData.completed_at).toLocaleString()}</span>
            </div>`;
    }
    
    if (taskData.archived) {
        html += `
            <div class="metadata-item">
                <label>Status:</label>
                <span class="archived-badge">Archived</span>
            </div>`;
    }
    
    html += `</div>`;
    return html;
}

function renderNoteDetails(node) {
    const noteData = node.note_data || {};
    let content = '<em>No content</em>';
    
    if (noteData.body) {
        try {
            // Handle different marked.js API versions
            if (typeof marked === 'function') {
                content = marked(noteData.body);
            } else if (marked && typeof marked.parse === 'function') {
                content = marked.parse(noteData.body);
            } else {
                // Fallback to raw text with basic formatting
                content = noteData.body.replace(/\n/g, '<br>');
            }
        } catch (error) {
            console.warn('Markdown parsing failed, using plain text:', error);
            content = noteData.body.replace(/\n/g, '<br>');
        }
    }
    
    return `
        <div class="metadata-section">
            <h3>Note Content</h3>
            <div class="note-content-preview">
                ${content}
            </div>
        </div>
    `;
}

function renderSmartFolderDetails(node) {
    const smartFolderData = node.smart_folder_data || {};
    return `
        <div class="metadata-section">
            <h3>Smart Folder Rules</h3>
            <div class="rules-preview">
                ${JSON.stringify(smartFolderData.conditions || [], null, 2)}
            </div>
        </div>
    `;
}

function renderTemplateDetails(node) {
    return `
        <div class="metadata-section">
            <h3>Template Information</h3>
            <div class="metadata-item">
                <em>Template details to be implemented</em>
            </div>
        </div>
    `;
}

function renderGenericNodeDetails(node) {
    const parentNode = node.parent_id ? nodes[node.parent_id] : null;
    return `
        <div class="metadata-section">
            <h3>Node Information</h3>
            <div class="metadata-item">
                <label>Parent:</label>
                <span>${parentNode ? parentNode.title : 'Root level'}</span>
            </div>
            <div class="metadata-item">
                <label>Sort Order:</label>
                <span>${node.sort_order || 0}</span>
            </div>
        </div>
    `;
}

// Node-specific edit form renderers (to be implemented)
function renderTaskEditForm(node) {
    const taskData = node.task_data || {};
    
    // Format dates for separate date/time input fields (using local time)
    const formatDateForInput = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`; // YYYY-MM-DD in local time
    };
    
    const formatTimeForInput = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`; // HH:MM in local time
    };
    
    return `
        <div class="form-section">
            <label for="taskDescription">Description:</label>
            <textarea id="taskDescription" name="description" rows="4" placeholder="Task description...">${taskData.description || ''}</textarea>
        </div>
        <div class="form-section">
            <label for="taskStatus">Status:</label>
            <select id="taskStatus" name="status">
                <option value="todo">Todo</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
                <option value="dropped">Dropped</option>
            </select>
        </div>
        <div class="form-section">
            <label for="taskPriority">Priority:</label>
            <select id="taskPriority" name="priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
            </select>
        </div>
        <div class="form-section">
            <label>Due Date & Time:</label>
            <div class="date-time-inputs">
                <input type="date" id="taskDueDate" name="due_date" value="${formatDateForInput(taskData.due_at)}" placeholder="Date">
                <input type="time" id="taskDueTime" name="due_time" value="${formatTimeForInput(taskData.due_at)}">
            </div>
        </div>
        <div class="form-section">
            <label>Earliest Start Date & Time:</label>
            <div class="date-time-inputs">
                <input type="date" id="taskStartDate" name="start_date" value="${formatDateForInput(taskData.earliest_start_at)}" placeholder="Date">
                <input type="time" id="taskStartTime" name="start_time" value="${formatTimeForInput(taskData.earliest_start_at)}">
            </div>
        </div>
        <div class="form-section">
            <label for="taskParent">Parent Folder:</label>
            <select id="taskParent" name="parent_id">
                ${buildParentOptions(node)}
            </select>
        </div>
        <div class="form-section">
            <label for="taskSortOrder">Sort Order:</label>
            <input type="number" id="taskSortOrder" name="sort_order" value="${node.sort_order || 0}" min="0" placeholder="0">
            <small>Lower numbers appear first</small>
        </div>
        <div class="form-section">
            <label for="taskArchived">Archived:</label>
            <input type="checkbox" id="taskArchived" name="archived" ${taskData.archived ? 'checked' : ''}>
            <span class="checkbox-label">Archive this task</span>
        </div>
    `;
}

function renderNoteEditForm(node) {
    const noteData = node.note_data || {};
    return `
        <div class="form-section">
            <label for="noteBody">Content:</label>
            <textarea id="noteBody" name="body" rows="10" placeholder="Enter note content...">${noteData.body || ''}</textarea>
        </div>
    `;
}

function renderSmartFolderEditForm(node) {
    return `
        <div class="form-section">
            <label>Smart Folder Rules:</label>
            <div id="smartFolderRulesEditor">
                <em>Smart folder rules editor to be implemented</em>
            </div>
        </div>
    `;
}

function renderTemplateEditForm(node) {
    return `
        <div class="form-section">
            <label>Template Configuration:</label>
            <div id="templateEditor">
                <em>Template editor to be implemented</em>
            </div>
        </div>
    `;
}

function renderGenericNodeEditForm(node) {
    const parentOptions = buildParentOptions(node);
    
    const html = `
        <div class="form-section">
            <label for="nodeParent">Parent Folder:</label>
            <select id="nodeParent" name="parent_id">
                ${parentOptions}
            </select>
        </div>
        <div class="form-section">
            <label for="nodeSortOrder">Sort Order:</label>
            <input type="number" id="nodeSortOrder" name="sort_order" value="${node.sort_order || 0}" min="0" placeholder="0">
            <small>Lower numbers appear first</small>
        </div>
    `;
    
    return html;
}

// Build parent selection options for node editing
function buildParentOptions(currentNode) {
    let html = '<option value="">Root level</option>';
    
    // Get all possible parent nodes (folders including siblings, not the current node itself)
    const possibleParents = Object.values(nodes).filter(node => {
        // Exclude the current node to prevent circular references
        if (node.id === currentNode.id) return false;
        
        // Include all folder types: pure nodes and legacy container folders
        return node.node_type === 'node' || 
               node.node_type === 'folder' ||
               (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder');
    });
    
    // Sort by title
    possibleParents.sort((a, b) => a.title.localeCompare(b.title));
    
    possibleParents.forEach(parent => {
        const selected = parent.id === currentNode.parent_id ? 'selected' : '';
        html += `<option value="${parent.id}" ${selected}>${parent.title} 📁</option>`;
    });
    
    return html;
}

// Check for unsaved changes
function hasUnsavedChanges() {
    if (currentView !== 'edit' || !currentNodeId) return false;
    
    const node = nodes[currentNodeId];
    if (!node) return false;
    
    // Check if title has changed
    const titleInput = document.getElementById('nodeEditTitle');
    if (titleInput && titleInput.value !== node.title) return true;
    
    // Check node-specific changes
    switch (node.node_type) {
        case 'node':
            const sortOrderInput = document.getElementById('nodeSortOrder');
            const parentSelect = document.getElementById('nodeParent');
            return (sortOrderInput && parseInt(sortOrderInput.value) !== (node.sort_order || 0)) ||
                   (parentSelect && parentSelect.value !== (node.parent_id || ''));
            
        case 'task':
            const descriptionInput = document.getElementById('taskDescription');
            const statusSelect = document.getElementById('taskStatus');
            const prioritySelect = document.getElementById('taskPriority');
            const dueDateInput = document.getElementById('taskDueDate');
            const dueTimeInput = document.getElementById('taskDueTime');
            const startDateInput = document.getElementById('taskStartDate');
            const startTimeInput = document.getElementById('taskStartTime');
            const archivedInput = document.getElementById('taskArchived');
            const taskData = node.task_data || {};
            
            // Helper to extract date/time from ISO string for comparison
            const getDatePart = (isoString) => isoString ? new Date(isoString).toISOString().slice(0, 10) : '';
            const getTimePart = (isoString) => isoString ? new Date(isoString).toISOString().slice(11, 16) : '';
            
            return (descriptionInput && descriptionInput.value !== (taskData.description || '')) ||
                   (statusSelect && statusSelect.value !== taskData.status) ||
                   (prioritySelect && prioritySelect.value !== taskData.priority) ||
                   (dueDateInput && dueDateInput.value !== getDatePart(taskData.due_at)) ||
                   (dueTimeInput && dueTimeInput.value !== getTimePart(taskData.due_at)) ||
                   (startDateInput && startDateInput.value !== getDatePart(taskData.earliest_start_at)) ||
                   (startTimeInput && startTimeInput.value !== getTimePart(taskData.earliest_start_at)) ||
                   (archivedInput && archivedInput.checked !== (taskData.archived || false));
                   
        case 'note':
            const noteBody = document.getElementById('noteBody');
            const noteData = node.note_data || {};
            return noteBody && noteBody.value !== (noteData.body || '');
            
        default:
            return false;
    }
}

// Save node changes
export async function saveNodeChanges() {
    if (!currentNodeId || currentView !== 'edit') return;
    
    const node = nodes[currentNodeId];
    if (!node) return;
    
    // Collect form data
    const titleInput = document.getElementById('nodeEditTitle');
    const updatedNode = {
        ...node,
        title: titleInput ? titleInput.value : node.title
    };
    
    // Check if this is a folder (either pure node or legacy container)
    const isFolder = (node.node_type === 'node') || 
                    (node.node_type === 'folder') ||
                    (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder');
    
    if (isFolder) {
        // Handle folder-specific fields
        const sortOrderInput = document.getElementById('nodeSortOrder');
        const parentSelect = document.getElementById('nodeParent');
        updatedNode.sort_order = sortOrderInput ? parseInt(sortOrderInput.value) : node.sort_order;
        updatedNode.parent_id = parentSelect ? (parentSelect.value || null) : node.parent_id;
    }
    
    // Collect node-specific data for non-folders
    if (!isFolder) {
        switch (node.node_type) {
            case 'task':
                const descriptionInput = document.getElementById('taskDescription');
                const statusSelect = document.getElementById('taskStatus');
                const prioritySelect = document.getElementById('taskPriority');
                const dueDateInput = document.getElementById('taskDueDate');
                const dueTimeInput = document.getElementById('taskDueTime');
                const startDateInput = document.getElementById('taskStartDate');
                const startTimeInput = document.getElementById('taskStartTime');
                const parentSelect = document.getElementById('taskParent');
                const sortOrderInput = document.getElementById('taskSortOrder');
                const archivedInput = document.getElementById('taskArchived');
                
                // Combine date and time into ISO string
                const combineDateTimeToISO = (dateValue, timeValue) => {
                    if (!dateValue) return null;
                    const dateTime = timeValue ? `${dateValue}T${timeValue}:00` : `${dateValue}T00:00:00`;
                    return new Date(dateTime).toISOString();
                };
                
                const newDueAt = combineDateTimeToISO(dueDateInput?.value, dueTimeInput?.value);
                const newStartAt = combineDateTimeToISO(startDateInput?.value, startTimeInput?.value);
                const newStatus = statusSelect?.value || node.task_data?.status || 'todo';
                const newPriority = prioritySelect?.value || node.task_data?.priority || 'medium';
                
                // Handle multiple status dropdowns - find the one that's not "todo"
                const allStatusSelects = document.querySelectorAll('#taskStatus');
                const allPrioritySelects = document.querySelectorAll('#taskPriority');
                
                // Get the actual selected values from all dropdowns
                const statusValues = Array.from(allStatusSelects).map(s => s.value);
                const priorityValues = Array.from(allPrioritySelects).map(s => s.value);
                
                // Use the non-default status value if any dropdown has it
                const actualStatus = statusValues.find(val => val !== 'todo') || statusValues[0] || 'todo';
                const actualPriority = priorityValues[0] || 'medium'; // Priority works fine, just use first
                
                // Update both node-level and task-specific data
                updatedNode.parent_id = parentSelect ? (parentSelect.value || null) : node.parent_id;
                updatedNode.sort_order = sortOrderInput ? parseInt(sortOrderInput.value) : node.sort_order;
                updatedNode.task_data = {
                    ...node.task_data,
                    description: descriptionInput?.value || node.task_data?.description || null,
                    status: actualStatus,
                    priority: actualPriority,
                    due_at: newDueAt !== null ? newDueAt : node.task_data?.due_at,
                    earliest_start_at: newStartAt !== null ? newStartAt : node.task_data?.earliest_start_at,
                    archived: archivedInput ? archivedInput.checked : (node.task_data?.archived || false),
                    // Set completed_at when status changes to done
                    completed_at: (newStatus === 'done' && node.task_data?.status !== 'done') ? new Date().toISOString() : node.task_data?.completed_at
                };
                break;
                
            case 'note':
                const noteBody = document.getElementById('noteBody');
                updatedNode.note_data = {
                    ...node.note_data,
                    body: noteBody ? noteBody.value : node.note_data?.body
                };
                break;
        }
    }
    
    // Save to server
    console.log('Saving node changes:', {
        nodeId: currentNodeId,
        originalTaskData: node.task_data,
        updatedTaskData: updatedNode.task_data,
        isFolder: isFolder
    });
    
    try {
        const requestBody = JSON.stringify(updatedNode);
        console.log('Request body being sent:', requestBody);
        
        const response = await fetch(`${API_BASE}/nodes/${currentNodeId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: requestBody
        });
        
        
        console.log('API response status:', response.status);
        
        if (response.ok) {
            const savedNode = await response.json();
            console.log('Saved task data response:', savedNode.task_data);
            nodes[currentNodeId] = savedNode;
            
            // Navigate back to details view with fresh data
            navigateToDetails(currentNodeId);
            
            // Always refresh the tree to show updated sort order
            renderTree();
        } else {
            const errorText = await response.text();
            console.error('Save failed:', response.status, errorText);
            alert('Failed to save changes: ' + errorText);
        }
    } catch (error) {
        console.error('Failed to save node:', error);
        alert('Failed to save changes');
    }
}

// Initialize navigation system
export function initializeNavigation() {
    try {
        // Create page containers
        createDetailsPageContainer();
        createEditPageContainer();
        
        // Clear navigation stack
        clearNavigationStack();
        
        // Set initial state
        setCurrentView('focus');
        setCurrentNodeId(null);
    } catch (error) {
        console.error('Error initializing navigation system:', error);
    }
}

// Global function bindings for HTML onclick handlers
window.navigateToFocus = navigateToFocus;
window.navigateToDetails = navigateToDetails;
window.navigateToEdit = navigateToEdit;
window.navigateBack = navigateBack;
window.navigateWithUnsavedCheck = navigateWithUnsavedCheck;
window.saveNodeChanges = saveNodeChanges;
window.deleteNodeFromDetails = deleteNodeFromDetails;

// Function to remove a tag from a node
async function removeTagFromNode(nodeId, tagId) {
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
            
            // Re-render the details page to show updated tags
            renderDetailsPage(nodeId);
        } else {
            alert('Failed to remove tag');
        }
    } catch (error) {
        console.error('Error removing tag:', error);
        alert('Error removing tag');
    }
}

window.removeTagFromNode = removeTagFromNode;

// These functions are already bound globally in main.js
// window.logout = logout;
// window.toggleDarkMode = toggleDarkMode;  
// window.toggleFloatingChat = toggleFloatingChat;