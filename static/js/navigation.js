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
    
    const isTestMode = nodeId === 'test-rule-node' || nodeId?.startsWith('test-rule-') || nodeId?.startsWith('sample-');
    
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
    
    // For test mode, replace the header with Test Rule Manager
    if (isTestMode && node.node_type === 'smart_folder') {
        const pageHeader = container.querySelector('.page-header');
        if (pageHeader) {
            pageHeader.innerHTML = '';
            pageHeader.style.display = 'none';
        }
        
        // Add Test Rule Manager at the top of content
        contentArea.innerHTML = renderTestRuleManager() + renderNodeEditForm(node);
        
        // Initialize the smart folder editor
        setTimeout(() => {
            if (typeof window.initializeSmartFolderEditor === 'function') {
                window.initializeSmartFolderEditor(node);
            }
            
            // Update the name field
            const nameField = document.getElementById('testRuleName');
            if (nameField) {
                nameField.value = node.title;
            }
            
            // Show test controls
            const testControls = document.getElementById('testRuleControls');
            if (testControls) {
                testControls.style.display = 'block';
            }
        }, 100);
        
        return;
    }
    
    // Update header for non-test mode
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
    const rules = smartFolderData.rules || {};
    
    let rulesHtml = '';
    if (rules.logic && rules.conditions) {
        rulesHtml = `
            <div class="rules-display">
                <div class="rule-logic">
                    <strong>Logic:</strong> ${rules.logic}
                </div>
                <div class="rule-conditions">
                    <strong>Conditions:</strong>
                    <ul>
                        ${rules.conditions.map(cond => `
                            <li>
                                <span class="condition-type">${cond.type}</span>
                                <span class="condition-operator">${cond.operator}</span>
                                <span class="condition-values">${JSON.stringify(cond.values)}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            </div>
        `;
    } else {
        rulesHtml = '<div class="no-rules">No rules defined</div>';
    }
    
    return `
        <div class="metadata-section">
            <h3>Smart Folder Rules</h3>
            ${rulesHtml}
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
    const rules = node.smart_folder_data?.rules || { conditions: [], logic: "AND" };
    
    // Initialize the editor after a short delay to ensure DOM is ready
    setTimeout(() => {
        if (typeof window.initializeSmartFolderEditor === 'function') {
            window.initializeSmartFolderEditor(node);
        }
    }, 100);
    
    return `
        <div class="form-section">
            <label>Smart Folder Rules:</label>
            <div id="smartFolderRulesEditor">
                <div class="rules-logic-section">
                    <label for="rulesLogic">Match:</label>
                    <select id="rulesLogic" class="rules-logic-select">
                        <option value="AND" ${rules.logic === "AND" ? "selected" : ""}>All conditions</option>
                        <option value="OR" ${rules.logic === "OR" ? "selected" : ""}>Any condition</option>
                    </select>
                </div>
                
                <div id="conditionsList" class="conditions-list">
                    ${rules.conditions.map((condition, index) => renderConditionEditor(condition, index)).join('')}
                </div>
                
                <div class="add-condition-section">
                    <button type="button" class="add-condition-btn" onclick="addCondition()">+ Add Condition</button>
                </div>
                
                <div class="preview-section">
                    <button type="button" class="preview-btn" onclick="previewSmartFolder()">Preview Results</button>
                    <div id="previewResults" class="preview-results hidden"></div>
                </div>
            </div>
            
            <!-- Test Controls for Rule Parser Development -->
            <div id="testRuleControls" style="display: none; margin-top: 20px; padding: 15px; background: #fffbf0; border: 2px solid #ff6b6b; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #ff6b6b;">🧪 Test Rule Parser Controls</h4>
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <button type="button" onclick="showCurrentJSON()" style="padding: 8px 15px; background: #007AFF; color: white; border: none; border-radius: 4px; cursor: pointer;">Show Current JSON</button>
                    <button type="button" onclick="testJSONToForm()" style="padding: 8px 15px; background: #34C759; color: white; border: none; border-radius: 4px; cursor: pointer;">Test JSON → Form</button>
                    <button type="button" onclick="testFormToJSON()" style="padding: 8px 15px; background: #FF9500; color: white; border: none; border-radius: 4px; cursor: pointer;">Test Form → JSON</button>
                </div>
                <div id="testOutput" style="background: #f8f9fa; color: #212529; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; border: 1px solid #dee2e6;"></div>
            </div>
        </div>
    `;
}

function renderConditionEditor(condition, index) {
    // Get available smart folders for "Existing Rule" option
    const availableRules = getAvailableSmartFolders();
    
    const conditionTypes = [
        { value: "node_type", label: "Node Type" },
        { value: "task_status", label: "Task Status" },
        { value: "task_priority", label: "Task Priority" },
        { value: "due_date", label: "Due Date" },
        { value: "earliest_start", label: "Earliest Start Date" },
        { value: "tag_contains", label: "Has Tags" },
        { value: "title_contains", label: "Title Contains" },
        { value: "parent_node", label: "Parent Node" }
    ];
    
    // Add "Existing Filter" option if there are available rules
    if (availableRules.length > 0) {
        conditionTypes.push({ value: "saved_filter", label: "Existing Filter" });
    }
    
    const operators = getOperatorsForConditionType(condition.type || "node_type");
    
    return `
        <div class="condition-editor" data-condition-index="${index}">
            <div class="condition-header">
                <select class="condition-type-select" onchange="onConditionTypeChange(${index}, this.value)">
                    ${conditionTypes.map(type => `
                        <option value="${type.value}" ${condition.type === type.value ? "selected" : ""}>
                            ${type.label}
                        </option>
                    `).join('')}
                </select>
                
                <select class="condition-operator-select">
                    ${operators.map(op => `
                        <option value="${op.value}" ${condition.operator === op.value ? "selected" : ""}>
                            ${op.label}
                        </option>
                    `).join('')}
                </select>
                
                <button type="button" class="remove-condition-btn" onclick="removeCondition(${index})">×</button>
            </div>
            
            <div class="condition-values">
                ${renderConditionValues(condition, index)}
            </div>
        </div>
    `;
}

function renderConditionValues(condition, index) {
    const conditionType = condition.type || "node_type";
    const values = condition.values || [];
    
    switch (conditionType) {
        case "node_type":
            const nodeTypes = ["task", "note", "folder", "smart_folder"];
            return `
                <div class="checkbox-group">
                    ${nodeTypes.map(type => `
                        <label class="checkbox-label">
                            <input type="checkbox" value="${type}" 
                                ${values.includes(type) ? "checked" : ""}>
                            ${type.charAt(0).toUpperCase() + type.slice(1)}
                        </label>
                    `).join('')}
                </div>
            `;
            
        case "task_status":
            const statuses = ["todo", "in_progress", "done", "dropped"];
            return `
                <div class="checkbox-group">
                    ${statuses.map(status => `
                        <label class="checkbox-label">
                            <input type="checkbox" value="${status}" 
                                ${values.includes(status) ? "checked" : ""}>
                            ${status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </label>
                    `).join('')}
                </div>
            `;
            
        case "task_priority":
            const priorities = ["low", "medium", "high", "urgent"];
            return `
                <div class="checkbox-group">
                    ${priorities.map(priority => `
                        <label class="checkbox-label">
                            <input type="checkbox" value="${priority}" 
                                ${values.includes(priority) ? "checked" : ""}>
                            ${priority.charAt(0).toUpperCase() + priority.slice(1)}
                        </label>
                    `).join('')}
                </div>
            `;
            
        case "due_date":
        case "earliest_start":
            return `
                <div class="date-inputs">
                    <input type="date" class="date-input" value="${values[0] || ''}" 
                        placeholder="Select date">
                    ${condition.operator === "between" ? `
                        <span class="date-separator">to</span>
                        <input type="date" class="date-input" value="${values[1] || ''}" 
                            placeholder="End date">
                    ` : ''}
                </div>
            `;
            
        case "title_contains":
            return `
                <input type="text" class="text-input" value="${values[0] || ''}" 
                    placeholder="Enter text to search for">
            `;
            
        case "tag_contains":
            return `
                <div class="tag-selector">
                    <input type="text" class="tag-search-input" placeholder="Start typing to search tags..."
                        onkeyup="searchTagsForCondition(${index}, this.value)">
                    <div class="selected-tags" id="selectedTags${index}">
                        ${(values || []).map(tagId => renderSelectedTag(tagId, index)).join('')}
                    </div>
                    <div class="tag-suggestions hidden" id="tagSuggestions${index}"></div>
                </div>
            `;
            
        case "parent_node":
            return `
                <div class="node-selector">
                    <input type="text" class="node-search-input" placeholder="Start typing to search nodes..."
                        onkeyup="searchNodesForCondition(${index}, this.value)">
                    <div class="selected-nodes" id="selectedNodes${index}">
                        ${(values || []).map(nodeId => renderSelectedNode(nodeId, index)).join('')}
                    </div>
                    <div class="node-suggestions hidden" id="nodeSuggestions${index}"></div>
                </div>
            `;
            
        case "saved_filter":
            const availableRules = getAvailableSmartFolders();
            const selectedRule = values[0] || '';
            return `
                <select class="rule-select" style="width: 100%; padding: 8px; border: 1px solid #d1d1d6; border-radius: 4px;">
                    <option value="">Select a filter...</option>
                    ${availableRules.map(rule => `
                        <option value="${rule.id}" ${selectedRule === rule.id ? 'selected' : ''}>
                            ${rule.title}
                        </option>
                    `).join('')}
                </select>
            `;
            
        default:
            return `<input type="text" class="text-input" value="${values[0] || ''}" placeholder="Enter value">`;
    }
}

function getOperatorsForConditionType(conditionType) {
    switch (conditionType) {
        case "node_type":
        case "task_status":
        case "task_priority":
        case "tag_contains":
            return [
                { value: "in", label: "is any of" },
                { value: "not_in", label: "is not any of" }
            ];
            
        case "due_date":
        case "earliest_start":
            return [
                { value: "before", label: "before" },
                { value: "after", label: "after" },
                { value: "on", label: "on" },
                { value: "between", label: "between" },
                { value: "is_null", label: "is not set" },
                { value: "is_not_null", label: "is set" }
            ];
            
        case "title_contains":
            return [
                { value: "contains", label: "contains" },
                { value: "not_contains", label: "does not contain" },
                { value: "equals", label: "equals" },
                { value: "starts_with", label: "starts with" },
                { value: "ends_with", label: "ends with" }
            ];
            
        case "parent_node":
            return [
                { value: "equals", label: "is" },
                { value: "in", label: "is any of" },
                { value: "not_equals", label: "is not" },
                { value: "not_in", label: "is not any of" }
            ];
            
        case "saved_filter":
            return [
                { value: "matches", label: "matches" },
                { value: "not_matches", label: "does not match" }
            ];
            
        default:
            return [
                { value: "equals", label: "equals" },
                { value: "contains", label: "contains" }
            ];
    }
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
            
        case 'smart_folder':
            // Check if smart folder rules have changed
            if (typeof collectSmartFolderRules === 'function') {
                const currentRules = collectSmartFolderRules();
                const originalRules = node.smart_folder_data?.rules || { conditions: [], logic: "AND" };
                return JSON.stringify(currentRules) !== JSON.stringify(originalRules);
            }
            return false;
            
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
                
            case 'smart_folder':
                // Collect smart folder rules
                if (typeof collectSmartFolderRules === 'function') {
                    const rules = collectSmartFolderRules();
                    
                    // Check if we need to create or update a rule
                    if (window.RulesAPI) {
                        try {
                            let ruleId = node.smart_folder_data?.rule_id;
                            
                            if (ruleId) {
                                // Update existing rule
                                await window.RulesAPI.updateRule(ruleId, {
                                    name: `${updatedNode.title} Rules`,
                                    rule_data: rules
                                });
                            } else {
                                // Create new rule and link it
                                const newRule = await window.RulesAPI.createRule({
                                    name: `${updatedNode.title} Rules`,
                                    description: `Auto-generated rules for ${updatedNode.title}`,
                                    rule_data: rules,
                                    is_public: false
                                });
                                ruleId = newRule.id;
                            }
                            
                            updatedNode.smart_folder_data = {
                                ...node.smart_folder_data,
                                rule_id: ruleId,
                                rules: rules  // Keep for backward compatibility
                            };
                        } catch (error) {
                            console.error('Error managing rule:', error);
                            // Fallback to old behavior
                            updatedNode.smart_folder_data = {
                                ...node.smart_folder_data,
                                rules: rules
                            };
                        }
                    } else {
                        // Fallback if Rules API not available
                        updatedNode.smart_folder_data = {
                            ...node.smart_folder_data,
                            rules: rules
                        };
                    }
                }
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

// Smart Folder Rules Editor Functions
let currentSmartFolderConditions = [];

window.addCondition = function() {
    const newCondition = {
        type: "node_type",
        operator: "in",
        values: []
    };
    
    currentSmartFolderConditions.push(newCondition);
    refreshConditionsList();
};

window.removeCondition = function(index) {
    currentSmartFolderConditions.splice(index, 1);
    refreshConditionsList();
};

window.onConditionTypeChange = function(index, newType) {
    if (currentSmartFolderConditions[index]) {
        currentSmartFolderConditions[index].type = newType;
        currentSmartFolderConditions[index].operator = getOperatorsForConditionType(newType)[0].value;
        currentSmartFolderConditions[index].values = [];
        refreshConditionsList();
    }
};

function refreshConditionsList() {
    const conditionsList = document.getElementById('conditionsList');
    if (conditionsList) {
        conditionsList.innerHTML = currentSmartFolderConditions
            .map((condition, index) => renderConditionEditor(condition, index))
            .join('');
    }
}

window.previewSmartFolder = function() {
    const rules = collectSmartFolderRules();
    console.log('Preview rules:', rules);
    
    // TODO: Call API to preview results
    const previewResults = document.getElementById('previewResults');
    if (previewResults) {
        previewResults.innerHTML = '<div class="loading">Loading preview...</div>';
        previewResults.classList.remove('hidden');
        
        // Call the preview API
        fetch(`${API_BASE}/nodes/smart_folder/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(rules)
        })
        .then(response => response.json())
        .then(results => {
            if (results.length === 0) {
                previewResults.innerHTML = '<div class="preview-empty">No results found</div>';
            } else {
                previewResults.innerHTML = `
                    <div class="preview-header">${results.length} result(s) found:</div>
                    <div class="preview-items">
                        ${results.slice(0, 5).map(node => `
                            <div class="preview-item">
                                <span class="preview-icon">${getNodeIcon(node.node_type)}</span>
                                <span class="preview-title">${node.title}</span>
                                <span class="preview-type">${node.node_type}</span>
                            </div>
                        `).join('')}
                        ${results.length > 5 ? `<div class="preview-more">... and ${results.length - 5} more</div>` : ''}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Preview error:', error);
            previewResults.innerHTML = '<div class="preview-error">Error loading preview</div>';
        });
    }
};

window.collectSmartFolderRules = function() {
    console.log('=== collectSmartFolderRules ===');
    
    const logic = document.getElementById('rulesLogic')?.value || 'AND';
    console.log('Logic:', logic);
    
    const conditions = [];
    
    document.querySelectorAll('.condition-editor').forEach((conditionEl, index) => {
        const condition = currentSmartFolderConditions[index];
        if (!condition) {
            console.log(`Skipping index ${index} - no condition in currentSmartFolderConditions`);
            return;
        }
        
        const typeSelect = conditionEl.querySelector('.condition-type-select');
        const operatorSelect = conditionEl.querySelector('.condition-operator-select');
        
        console.log(`Condition ${index}:`, {
            type: typeSelect?.value,
            operator: operatorSelect?.value,
            originalCondition: condition
        });
        
        const collectedCondition = {
            type: typeSelect.value,
            operator: operatorSelect.value,
            values: collectConditionValues(conditionEl, typeSelect.value)
        };
        
        console.log(`Collected values for condition ${index}:`, collectedCondition.values);
        
        if (collectedCondition.values.length > 0 || ['is_null', 'is_not_null'].includes(collectedCondition.operator)) {
            conditions.push(collectedCondition);
        } else {
            console.log(`Skipping condition ${index} - no values and not a null operator`);
        }
    });
    
    const result = { conditions, logic };
    console.log('Final collected rules:', JSON.stringify(result, null, 2));
    console.log('=== End collectSmartFolderRules ===');
    
    return result;
}

function collectConditionValues(conditionEl, conditionType) {
    switch (conditionType) {
        case "saved_filter":
            const ruleSelect = conditionEl.querySelector('.rule-select');
            return ruleSelect && ruleSelect.value ? [ruleSelect.value] : [];
            
        case "node_type":
        case "task_status":
        case "task_priority":
            return Array.from(conditionEl.querySelectorAll('.checkbox-group input:checked'))
                .map(input => input.value);
                
        case "due_date":
        case "earliest_start":
            const dateInputs = conditionEl.querySelectorAll('.date-input');
            return Array.from(dateInputs)
                .map(input => input.value)
                .filter(value => value);
                
        case "title_contains":
            const textInput = conditionEl.querySelector('.text-input');
            return textInput && textInput.value ? [textInput.value] : [];
            
        case "tag_contains":
            return Array.from(conditionEl.querySelectorAll('.selected-tags .selected-tag'))
                .map(tag => tag.getAttribute('data-tag-id'))
                .filter(id => id);
                
        case "parent_node":
            return Array.from(conditionEl.querySelectorAll('.selected-nodes .selected-node'))
                .map(node => node.getAttribute('data-node-id'))
                .filter(id => id);
                
        default:
            const defaultInput = conditionEl.querySelector('.text-input');
            return defaultInput && defaultInput.value ? [defaultInput.value] : [];
    }
}

function renderSelectedTag(tagId, conditionIndex) {
    // This would need to be implemented to show selected tags
    // For now, return a placeholder
    return `<span class="selected-tag" data-tag-id="${tagId}">Tag ${tagId} <button onclick="removeTagFromCondition(${conditionIndex}, '${tagId}')">×</button></span>`;
}

function renderSelectedNode(nodeId, conditionIndex) {
    // This would need to be implemented to show selected nodes
    // For now, return a placeholder
    return `<span class="selected-node" data-node-id="${nodeId}">Node ${nodeId} <button onclick="removeNodeFromCondition(${conditionIndex}, '${nodeId}')">×</button></span>`;
}

function getNodeIcon(nodeType) {
    switch (nodeType) {
        case 'task': return '☐';
        case 'note': return '📝';
        case 'folder': return '📁';
        case 'smart_folder': return '🔍';
        default: return '•';
    }
}

// Get available smart folders for rule references (excluding current one to prevent circular references)
function getAvailableSmartFolders() {
    // Get the ID of the smart folder currently being edited
    const editingNodeId = window.currentNodeId || nodes['test-rule-node']?.id;
    
    // Filter for smart folders, excluding the current one
    const smartFolders = Object.values(nodes).filter(node => {
        return node.node_type === 'smart_folder' && 
               node.id !== editingNodeId &&
               node.smart_folder_data?.rules?.conditions?.length > 0;  // Only include rules with conditions
    });
    
    // Sort by title for better UX
    smartFolders.sort((a, b) => a.title.localeCompare(b.title));
    
    console.log('Available smart folders for rules:', smartFolders.map(sf => ({ id: sf.id, title: sf.title })));
    
    return smartFolders;
}

// Initialize smart folder conditions when editing
window.initializeSmartFolderEditor = async function(node) {
    console.log('=== initializeSmartFolderEditor ===');
    console.log('Node:', node);
    
    let rules = node.smart_folder_data?.rules || { conditions: [], logic: "AND" };
    
    // If the smart folder has a rule_id, load the rule from the API
    if (node.smart_folder_data?.rule_id && window.RulesAPI) {
        try {
            const rule = await window.RulesAPI.getRule(node.smart_folder_data.rule_id);
            if (rule && rule.rule_data) {
                rules = rule.rule_data;
                console.log('Loaded rules from Rules API:', JSON.stringify(rules, null, 2));
            }
        } catch (error) {
            console.error('Error loading rule:', error);
            // Fall back to embedded rules
        }
    }
    
    console.log('Rules to use:', JSON.stringify(rules, null, 2));
    
    currentSmartFolderConditions = [...rules.conditions];
    console.log('Current conditions after copy:', currentSmartFolderConditions);
    
    // Set logic selector
    const logicSelector = document.getElementById('rulesLogic');
    if (logicSelector) {
        logicSelector.value = rules.logic || 'AND';
    }
    
    // Set initial state if no conditions exist
    if (currentSmartFolderConditions.length === 0) {
        console.log('No conditions found, adding default');
        addCondition();
    } else {
        console.log('Refreshing conditions list with existing conditions');
        // Refresh the display to show existing conditions
        refreshConditionsList();
    }
    
    console.log('=== End initializeSmartFolderEditor ===');
};

// These functions are already bound globally in main.js
// window.logout = logout;
// window.toggleDarkMode = toggleDarkMode;  
// window.toggleFloatingChat = toggleFloatingChat;

// Test helper functions - define early so they're available when HTML is rendered
window.showCurrentJSON = function() {
    console.log('showCurrentJSON called');
    const output = document.getElementById('testOutput');
    if (!output) {
        console.error('testOutput element not found');
        return;
    }
    
    // Make sure the function is available
    if (typeof window.collectSmartFolderRules !== 'function') {
        console.error('collectSmartFolderRules not found');
        output.textContent = 'Error: collectSmartFolderRules function not available';
        return;
    }
    
    try {
        const currentRules = window.collectSmartFolderRules();
        console.log('Collected rules:', currentRules);
        output.textContent = '=== Current Form State as JSON ===\n' + 
                            JSON.stringify(currentRules, null, 2);
        // Force visibility and handle dark mode
        output.style.display = 'block';
        output.style.minHeight = '100px';
        
        // Check if dark mode is active
        const isDarkMode = document.body.classList.contains('dark-mode');
        if (isDarkMode) {
            output.style.background = '#2d2d30';
            output.style.color = '#cccccc';
            output.style.border = '1px solid #555';
        } else {
            output.style.background = '#f8f9fa';
            output.style.color = '#212529';
            output.style.border = '1px solid #dee2e6';
        }
    } catch (error) {
        console.error('Error collecting rules:', error);
        output.textContent = 'Error collecting rules: ' + error.message;
    }
};

window.testJSONToForm = function() {
    const output = document.getElementById('testOutput');
    if (!output) return;
    
    // Get the test node using currentNodeId
    const testNode = nodes[window.currentNodeId];
    if (!testNode) {
        output.textContent = 'Error: Current node not found';
        return;
    }
    
    const originalJSON = testNode.smart_folder_data.rules;
    output.textContent = '=== Testing JSON → Form Conversion ===\n\n';
    output.textContent += 'Original JSON:\n' + JSON.stringify(originalJSON, null, 2) + '\n\n';
    
    // Re-initialize the editor with the original JSON
    initializeSmartFolderEditor(testNode);
    
    // After a short delay, collect the form state
    setTimeout(() => {
        const formState = collectSmartFolderRules();
        output.textContent += 'Form State after loading:\n' + JSON.stringify(formState, null, 2) + '\n\n';
        
        // Compare
        const match = JSON.stringify(originalJSON) === JSON.stringify(formState);
        output.textContent += match ? '✅ MATCH! JSON → Form conversion successful' : 
                                     '❌ MISMATCH! JSON → Form conversion failed';
    }, 300);
};

window.testFormToJSON = function() {
    const output = document.getElementById('testOutput');
    if (!output) return;
    
    output.textContent = '=== Testing Form → JSON Conversion ===\n\n';
    
    // Collect current form state
    const formState = collectSmartFolderRules();
    output.textContent += 'Current Form State:\n' + JSON.stringify(formState, null, 2) + '\n\n';
    
    // Create a new test node with this JSON
    const testJSON = formState;
    const currentNode = nodes[window.currentNodeId];
    const testNode = {
        ...currentNode,
        smart_folder_data: {
            rules: testJSON
        }
    };
    
    // Re-initialize with this JSON
    initializeSmartFolderEditor(testNode);
    
    // After a short delay, collect again
    setTimeout(() => {
        const newFormState = collectSmartFolderRules();
        output.textContent += 'Form State after reload:\n' + JSON.stringify(newFormState, null, 2) + '\n\n';
        
        // Compare
        const match = JSON.stringify(testJSON) === JSON.stringify(newFormState);
        output.textContent += match ? '✅ MATCH! Form → JSON → Form round-trip successful' : 
                                     '❌ MISMATCH! Form → JSON → Form round-trip failed';
    }, 300);
};

// Render test rule manager UI
function renderTestRuleManager() {
    // Show ALL smart folders, not just test ones
    const testRules = Object.values(nodes).filter(n => 
        n.node_type === 'smart_folder'
    ).sort((a, b) => a.title.localeCompare(b.title));
    
    return `
        <div style="margin-bottom: 20px; padding: 15px; background: #f0f8ff; border: 2px solid #007AFF; border-radius: 8px;">
            <h4 style="margin-top: 0; color: #007AFF;">🧪 Test Rule Manager</h4>
            
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: 600;">Select Rule:</label>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <select id="testRuleSelector" onchange="loadTestRule(this.value)" style="flex: 1; padding: 8px; border: 1px solid #d1d1d6; border-radius: 4px;">
                        <option value="">-- Select a test rule --</option>
                        ${testRules.map(rule => `
                            <option value="${rule.id}" ${rule.id === currentNodeId ? 'selected' : ''}>
                                ${rule.title}
                            </option>
                        `).join('')}
                    </select>
                    <button onclick="createNewTestRule()" style="padding: 8px 15px; background: #34C759; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        + New Rule
                    </button>
                    <button onclick="deleteCurrentTestRule()" style="padding: 8px 15px; background: #FF3B30; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🗑 Delete
                    </button>
                </div>
            </div>
            
            <div style="display: flex; gap: 10px; align-items: center;">
                <input type="text" id="testRuleName" placeholder="Rule name..." style="flex: 1; padding: 8px; border: 1px solid #d1d1d6; border-radius: 4px;">
                <button onclick="saveTestRule()" style="padding: 8px 15px; background: #007AFF; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    💾 Save Rule
                </button>
                <button onclick="duplicateTestRule()" style="padding: 8px 15px; background: #FF9500; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    📋 Duplicate
                </button>
            </div>
            
            <div id="testRuleFeedback" style="margin-top: 10px; padding: 8px; border-radius: 4px; display: none;"></div>
        </div>
    `;
}

// Test rule management functions
window.loadTestRule = function(ruleId) {
    if (!ruleId) return;
    
    const rule = nodes[ruleId];
    if (!rule || rule.node_type !== 'smart_folder') {
        showTestFeedback('Rule not found', 'error');
        return;
    }
    
    // Update current node
    window.currentNodeId = ruleId;
    
    // Re-render the entire edit page with the new rule
    setCurrentNodeId(ruleId);
    setCurrentView('edit');
    renderEditPage(ruleId);
    showPage('nodeEdit');
    
    // Update the name field after the page renders
    setTimeout(() => {
        const nameField = document.getElementById('testRuleName');
        if (nameField) {
            nameField.value = rule.title;
        }
        
        // Make sure the selector shows the correct rule
        const selector = document.getElementById('testRuleSelector');
        if (selector) {
            selector.value = ruleId;
        }
    }, 100);
    
    showTestFeedback(`Loaded: ${rule.title}`, 'success');
};

window.createNewTestRule = function() {
    // Prompt for rule name
    const ruleName = prompt('Enter name for new rule:', 'New Rule');
    if (!ruleName) {
        return; // User cancelled
    }
    
    const newId = `test-rule-${Date.now()}`;
    const newRule = {
        id: newId,
        title: ruleName,
        node_type: 'smart_folder',
        smart_folder_data: {
            rules: {
                logic: 'AND',
                conditions: []
            }
        }
    };
    
    // Add to nodes
    nodes[newId] = newRule;
    
    // Update current node ID and view state
    window.currentNodeId = newId;
    setCurrentNodeId(newId);
    setCurrentView('edit');
    
    // Re-render the entire edit page and show it
    renderEditPage(newId);
    showPage('nodeEdit');
    
    // Update the name field after rendering
    setTimeout(() => {
        const nameField = document.getElementById('testRuleName');
        if (nameField) {
            nameField.value = ruleName;
        }
        
        // Update selector to show new rule as selected
        const selector = document.getElementById('testRuleSelector');
        if (selector) {
            // Rebuild options
            const testRules = Object.values(nodes).filter(n => 
                n.node_type === 'smart_folder' && 
                (n.id?.startsWith('test-rule-') || n.id?.startsWith('sample-'))
            ).sort((a, b) => a.title.localeCompare(b.title));
            
            selector.innerHTML = '<option value="">-- Select a test rule --</option>' +
                testRules.map(rule => `
                    <option value="${rule.id}" ${rule.id === newId ? 'selected' : ''}>
                        ${rule.title}
                    </option>
                `).join('');
        }
    }, 100);
    
    showTestFeedback(`Created: ${ruleName}`, 'success');
};

window.saveTestRule = async function() {
    console.log('saveTestRule called');
    
    const nameField = document.getElementById('testRuleName');
    const ruleName = nameField?.value || 'Unnamed Rule';
    console.log('Rule name:', ruleName);
    
    // Collect current rules
    if (typeof window.collectSmartFolderRules !== 'function') {
        console.error('collectSmartFolderRules not available');
        showTestFeedback('Error: Cannot collect rules', 'error');
        return;
    }
    
    const rules = window.collectSmartFolderRules();
    console.log('Collected rules for saving:', rules);
    
    // Check if we're updating an existing database node or creating new
    let ruleId = window.currentNodeId;
    const isNewRule = !ruleId || ruleId === 'test-rule-node' || ruleId.startsWith('test-rule-') || ruleId.startsWith('sample-');
    
    try {
        let savedNode;
        
        if (isNewRule) {
            // Create new smart folder in database
            const newNode = {
                title: ruleName,
                node_type: 'smart_folder',
                parent_id: null,
                sort_order: 999,  // Put at end
                smart_folder_data: {
                    rules: rules
                }
            };
            
            console.log('Creating new smart folder in database:', newNode);
            
            const response = await fetch(`${API_BASE}/nodes/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newNode)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save: ${response.status}`);
            }
            
            savedNode = await response.json();
            console.log('Created in database with ID:', savedNode.id);
            
            // Update local nodes cache
            nodes[savedNode.id] = savedNode;
            window.currentNodeId = savedNode.id;
            
        } else {
            // Update existing smart folder
            const existingNode = nodes[ruleId];
            const updatedNode = {
                ...existingNode,
                title: ruleName,
                smart_folder_data: {
                    rules: rules
                }
            };
            
            console.log('Updating existing smart folder:', updatedNode);
            
            const response = await fetch(`${API_BASE}/nodes/${ruleId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedNode)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update: ${response.status}`);
            }
            
            savedNode = await response.json();
            console.log('Updated in database');
            
            // Update local cache
            nodes[ruleId] = savedNode;
        }
        
        // Refresh the entire nodes list to get all smart folders
        const nodesResponse = await fetch(`${API_BASE}/nodes/`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (nodesResponse.ok) {
            const allNodes = await nodesResponse.json();
            // Update nodes cache with all nodes
            allNodes.forEach(node => {
                nodes[node.id] = node;
            });
            console.log('Refreshed nodes cache');
        }
        
        // Update selector with all smart folders
        setTimeout(() => {
            const selector = document.getElementById('testRuleSelector');
            if (selector) {
                // Get ALL smart folders from database
                const allSmartFolders = Object.values(nodes).filter(n => 
                    n.node_type === 'smart_folder'
                ).sort((a, b) => a.title.localeCompare(b.title));
                
                console.log('Updating selector with all smart folders:', allSmartFolders.map(r => r.title));
                
                selector.innerHTML = '<option value="">-- Select a test rule --</option>' +
                    allSmartFolders.map(rule => `
                        <option value="${rule.id}" ${rule.id === savedNode.id ? 'selected' : ''}>
                            ${rule.title}
                        </option>
                    `).join('');
                
                selector.value = savedNode.id;  // Force selection
            }
        }, 100);
        
        showTestFeedback(`Saved to database: ${ruleName}`, 'success');
        console.log('Save to database complete');
        
    } catch (error) {
        console.error('Error saving to database:', error);
        showTestFeedback(`Error: ${error.message}`, 'error');
    }
};

window.deleteCurrentTestRule = function() {
    const ruleId = window.currentNodeId;
    if (!ruleId || ruleId === 'test-rule-node') {
        showTestFeedback('No rule selected to delete', 'error');
        return;
    }
    
    const rule = nodes[ruleId];
    if (!rule) {
        showTestFeedback('Rule not found', 'error');
        return;
    }
    
    if (!confirm(`Delete "${rule.title}"?`)) {
        return;
    }
    
    // Delete the rule
    delete nodes[ruleId];
    
    // Create a new rule
    createNewTestRule();
    
    showTestFeedback(`Deleted: ${rule.title}`, 'success');
};

window.duplicateTestRule = function() {
    const currentRule = nodes[window.currentNodeId];
    if (!currentRule) {
        showTestFeedback('No rule to duplicate', 'error');
        return;
    }
    
    const newId = `test-rule-${Date.now()}`;
    const newRule = {
        ...currentRule,
        id: newId,
        title: `${currentRule.title} (Copy)`,
        smart_folder_data: JSON.parse(JSON.stringify(currentRule.smart_folder_data))  // Deep copy
    };
    
    nodes[newId] = newRule;
    loadTestRule(newId);
    
    showTestFeedback(`Duplicated: ${currentRule.title}`, 'success');
};

function showTestFeedback(message, type) {
    const feedback = document.getElementById('testRuleFeedback');
    if (!feedback) return;
    
    feedback.textContent = message;
    feedback.style.display = 'block';
    feedback.style.background = type === 'success' ? '#d4edda' : '#f8d7da';
    feedback.style.color = type === 'success' ? '#155724' : '#721c24';
    feedback.style.border = `1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'}`;
    
    setTimeout(() => {
        feedback.style.display = 'none';
    }, 3000);
}

// Test Rule Editor function (temporary for development)
window.testRuleEditor = function() {
    // Create some sample smart folders for testing rule references
    const sampleSmartFolders = [
        {
            id: 'sample-high-priority',
            title: 'High Priority Tasks',
            node_type: 'smart_folder',
            smart_folder_data: {
                rules: {
                    logic: 'AND',
                    conditions: [
                        { type: 'node_type', operator: 'in', values: ['task'] },
                        { type: 'task_priority', operator: 'in', values: ['high', 'urgent'] }
                    ]
                }
            }
        },
        {
            id: 'sample-due-soon',
            title: 'Due This Week',
            node_type: 'smart_folder',
            smart_folder_data: {
                rules: {
                    logic: 'AND',
                    conditions: [
                        { type: 'node_type', operator: 'in', values: ['task'] },
                        { type: 'due_date', operator: 'between', values: ['2024-01-15', '2024-01-22'] }
                    ]
                }
            }
        },
        {
            id: 'sample-project-notes',
            title: 'Project Notes',
            node_type: 'smart_folder',
            smart_folder_data: {
                rules: {
                    logic: 'AND',
                    conditions: [
                        { type: 'node_type', operator: 'in', values: ['note'] },
                        { type: 'title_contains', operator: 'contains', values: ['project'] }
                    ]
                }
            }
        }
    ];
    
    // Add sample smart folders to nodes
    sampleSmartFolders.forEach(sf => {
        nodes[sf.id] = sf;
    });
    
    // Create a test smart folder node if it doesn't exist
    const testNodeId = 'test-rule-node';
    
    // Create test node with sample rules including a saved_rule reference
    const testNode = {
        id: testNodeId,
        title: 'TEST RULE PARSER',
        node_type: 'smart_folder',
        smart_folder_data: {
            rules: {
                logic: 'AND',
                conditions: [
                    {
                        type: 'saved_filter',
                        operator: 'matches',
                        values: ['sample-high-priority']  // Reference to High Priority Tasks
                    },
                    {
                        type: 'title_contains',
                        operator: 'contains',
                        values: ['urgent']
                    }
                ]
            }
        }
    };
    
    // Store in nodes temporarily
    nodes[testNodeId] = testNode;
    
    // Navigate to edit page with this test node
    setCurrentNodeId(testNodeId);
    setCurrentView('edit');
    renderEditPage(testNodeId);
    showPage('nodeEdit');
    
    // Show test controls and set initial name after a short delay
    setTimeout(() => {
        const testControls = document.getElementById('testRuleControls');
        if (testControls) {
            testControls.style.display = 'block';
        }
        
        const nameField = document.getElementById('testRuleName');
        if (nameField) {
            nameField.value = testNode.title;
        }
    }, 200);
    
    // Add console logging for debugging
    console.log('=== TEST RULE EDITOR ACTIVATED ===');
    console.log('Test JSON:', JSON.stringify(testNode.smart_folder_data.rules, null, 2));
    console.log('Use this page to test JSON <-> Form conversion');
    console.log('===================================');
};

// (Test helper functions moved earlier in the file)