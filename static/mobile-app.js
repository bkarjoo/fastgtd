        // Import state from modular state.js
        import { API_BASE, authToken, setAuthToken, nodes, setNodes, expandedNodes, currentRoot, setCurrentRoot, addType, setAddType as stateSetAddType, currentNoteId, setCurrentNoteId, clearState } from './js/state.js';
        
        // Import auth functions from modular auth.js
        import { login, logout, showMainApp, showLoginScreen } from './js/auth.js';
        
        // Import UI functions from modular ui.js
        import { initDarkMode, toggleDarkMode, getNodeIcon, backToMain, updateNavigation } from './js/ui.js';
        
        // Import settings functions from modular settings.js
        import { showSettings, editSettings, saveSettings } from './js/settings.js';
        
        // Import node functions from modular nodes.js
        import { loadNodes, refreshNodes, loadAllTags, renderTree, toggleExpand, handleNodeClick, handleFolderIconClick, exitFocusMode, toggleTaskComplete, createNode, deleteCurrentNode, editFocusedNodeTitle, handleFocusTitleClick } from './js/nodes.js';
        
        // Import creation functions from modular creation.js
        import { toggleAddForm, quickCreateFolder, quickCreateNote, quickCreateTask, quickCreateSmartFolder, quickCreateTemplate, useCurrentTemplate, loadParentOptions, setAddType } from './js/creation.js';
        
        // Import note functions from modular notes.js
        import { openNoteView, closeNoteView, editNote, cancelNoteEdit, saveNote } from './js/notes.js';
        
        // Import drag and drop functions from modular dragdrop.js
        import { initTouchDragAndDrop, handleDragStart, handleDragOver, handleDrop, handleDragEnd, handleDropOut, moveNode, moveNodeOut } from './js/dragdrop.js';
        
        // Import basic tag functions from modular tags.js
        import { showTagModal, hideTagModal, loadCurrentNodeTags } from './js/tags.js';
        
        // Import smart folder functions from modular smartfolders.js
        import { loadSmartFolderContents, refreshSmartFolderContents, refreshAllSmartFolders, loadSmartFolderContentsFocus } from './js/smartfolders.js';
        
        // Import chat functions from modular chat.js
        import { toggleFloatingChat, closeFloatingChat, sendChatMessage, sendToAI, updateAIContext, handleChatKeyPress } from './js/chat.js';

        // Initialize
        initDarkMode();
        if (authToken) {
            showMainApp();
            loadNodes();
        }
        
        // Initialize mobile-friendly drag and drop
        initTouchDragAndDrop();

        // initDarkMode now imported from ui.js

        // Make functions globally available for HTML onclick handlers
        window.login = login;
        window.logout = logout;
        window.toggleDarkMode = toggleDarkMode;
        window.toggleFloatingChat = toggleFloatingChat;
        window.closeFloatingChat = closeFloatingChat;
        window.quickCreateFolder = quickCreateFolder;
        window.quickCreateNote = quickCreateNote;
        window.quickCreateTask = quickCreateTask;
        window.quickCreateSmartFolder = quickCreateSmartFolder;
        window.quickCreateTemplate = quickCreateTemplate;
        window.showSettings = showSettings;
        window.editSettings = editSettings;
        window.saveSettings = saveSettings;
        window.backToMain = backToMain;

        // Import page state from state.js
        import { currentPage, setCurrentPage } from './js/state.js';
        
        // showSettings now imported from settings.js
        
        // backToMain now imported from ui.js
        
        // editSettings now imported from settings.js
        
        // getNodeIcon now imported from ui.js
        
        // populateDefaultNodeSelect now imported from settings.js
        
        // loadCurrentDefault now imported from settings.js
        
        // saveSettings now imported from settings.js
        
        // loadCurrentDefaultForDisplay now imported from settings.js
        
        // updateNavigation now imported from ui.js
        
        // Expose for inline handlers (extracted functions now bound in main.js)

        // loadNodes function now imported from nodes.js

        // refreshNodes function now imported from nodes.js

        // loadAllTags function now imported from nodes.js

        // renderTree now imported from nodes.js

        // loadSmartFolderContents now imported from smartfolders.js
        
        function navigateToParent(parentId) {
            console.log('Navigating to parent:', parentId); // Debug log
            // Navigate to focus mode on the parent folder
            const parentNode = nodes[parentId];
            if (parentNode) {
                // Set focus mode to the parent folder
                setCurrentRoot(parentId);
                updateAIContext();
                // Re-render the tree to show the parent folder in focus mode
                renderTree();
                // Update header buttons for the new focus mode
                updateHeaderButtons();
            }
        }

        // Smart folder loading functions now imported from smartfolders.js

        // toggleExpand now imported from nodes.js

        // handleNodeClick now imported from nodes.js

        // handleFolderIconClick now imported from nodes.js

        // exitFocusMode now imported from nodes.js

        // toggleTaskComplete now imported from nodes.js

        // toggleAddForm now imported from creation.js

        // quickCreateFolder now imported from creation.js

        // quickCreateNote now imported from creation.js

        // quickCreateTask now imported from creation.js

        // quickCreateSmartFolder now imported from creation.js

        // quickCreateTemplate now imported from creation.js

        // useCurrentTemplate now imported from creation.js

        // Smart folder variables
        let selectedTags = new Set();

        // loadParentOptions now imported from creation.js

        function toggleTaskSection() {
            const checkbox = document.getElementById('taskFilter');
            const section = document.getElementById('taskSection');
            section.classList.toggle('hidden', !checkbox.checked);
        }

        async function searchTags(query) {
            const resultsDiv = document.getElementById('tagResults');
            
            if (!query.trim()) {
                resultsDiv.classList.remove('active');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/tags/search?q=${encodeURIComponent(query)}&limit=10`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (response.ok) {
                    const tags = await response.json();
                    resultsDiv.innerHTML = '';
                    
                    tags.forEach(tag => {
                        if (!selectedTags.has(tag.id)) {
                            const div = document.createElement('div');
                            div.className = 'tag-option';
                            div.textContent = tag.name;
                            div.onclick = () => addTag(tag);
                            resultsDiv.appendChild(div);
                        }
                    });
                    
                    resultsDiv.classList.add('active');
                } else {
                    resultsDiv.classList.remove('active');
                }
            } catch (error) {
                console.error('Failed to search tags:', error);
            }
        }

        function addTag(tag) {
            selectedTags.add(tag.id);
            renderSelectedTags();
            document.getElementById('tagSearch').value = '';
            document.getElementById('tagResults').classList.remove('active');
        }

        function removeTag(tagId) {
            selectedTags.delete(tagId);
            renderSelectedTags();
        }

        function renderSelectedTags() {
            const container = document.getElementById('selectedTags');
            container.innerHTML = '';
            
            selectedTags.forEach(tagId => {
                const tag = allTags.find(t => t.id === tagId);
                if (tag) {
                    const div = document.createElement('div');
                    div.className = 'selected-tag';
                    div.innerHTML = `
                        <span>${tag.name}</span>
                        <span class="remove" onclick="removeTag('${tagId}')">×</span>
                    `;
                    container.appendChild(div);
                }
            });
        }

        let allTags = [];

        function buildSmartFolderRules() {
            const conditions = [];
            
            // Parent folder filter
            const parentId = document.getElementById('parentSelect').value;
            if (parentId) {
                conditions.push({
                    type: 'parent_node',
                    operator: 'equals',
                    values: [parentId]
                });
            }
            
            // Task filter
            const taskFilter = document.getElementById('taskFilter').checked;
            if (taskFilter) {
                conditions.push({
                    type: 'node_type',
                    operator: 'equals',
                    values: ['task']
                });
                
                // Task status filter
                const statusSelect = document.getElementById('taskStatus');
                const selectedStatuses = Array.from(statusSelect.selectedOptions).map(option => option.value);
                if (selectedStatuses.length > 0) {
                    conditions.push({
                        type: 'task_status',
                        operator: 'in',
                        values: selectedStatuses
                    });
                }
            }
            
            // Tag filter
            if (selectedTags.size > 0) {
                conditions.push({
                    type: 'tag_contains',
                    operator: 'any',
                    values: Array.from(selectedTags)
                });
            }
            
            return {
                conditions: conditions,
                logic: 'AND'
            };
        }

        // setAddType now imported from creation.js

        // createNode now imported from nodes.js

        // deleteCurrentNode now imported from nodes.js

        // editFocusedNodeTitle now imported from nodes.js

        // handleFocusTitleClick now imported from nodes.js

        // Note View Functions
        // currentNoteId now imported from state.js

        // openNoteView now imported from notes.js

        // closeNoteView now imported from notes.js

        // editNote now imported from notes.js

        // cancelNoteEdit now imported from notes.js

        // saveNote now imported from notes.js

        // initTouchDragAndDrop now imported from dragdrop.js
        
        // handleDragStart now imported from dragdrop.js
        
        // handleDragOver now imported from dragdrop.js
        
        // handleDrop now imported from dragdrop.js
        
        // handleDragEnd now imported from dragdrop.js
        
        // handleDropOut now imported from dragdrop.js
        
        // moveNodeOut now imported from dragdrop.js
        
        // moveNode now imported from dragdrop.js

        // toggleDarkMode now imported from ui.js


        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Header button management
        function updateHeaderButtons() {
            // If we're on settings page, don't update the navigation
            if (currentPage === 'settings') {
                return;
            }
            
            const navRight = document.getElementById('mainNavRight');
            if (!navRight) {
                console.error('mainNavRight element not found');
                return;
            }
            
            if (currentRoot) {
                // Check if we're inside a template
                const currentNode = nodes[currentRoot];
                const isInsideTemplate = currentNode && currentNode.node_type === 'template';
                
                // In focus mode - show tag button (hide template button if inside template, show use template button instead)
                navRight.innerHTML = `
                    <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                    <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                    <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
                    <button onclick="quickCreateNote()" title="Create Note">📝</button>
                    <button onclick="quickCreateTask()" title="Create Task">✅</button>
                    <button onclick="quickCreateSmartFolder()" title="Create Smart Folder">💎</button>
                    ${!isInsideTemplate ? '<button onclick="quickCreateTemplate()" title="Create Template">📦</button>' : '<button onclick="useCurrentTemplate()" title="Use This Template" style="color: #34C759;">✨</button>'}
                    <button onclick="showTagModal()" title="Add Tags" style="color: #007AFF;">🏷️</button>
                    <button onclick="showSettings()" title="Settings">⚙️</button>
                    <button onclick="logout()" title="Logout">🚪</button>
                `;
            } else {
                // In root mode - normal buttons
                navRight.innerHTML = `
                    <button onclick="toggleFloatingChat()" title="Ask AI Assistant">🤖</button>
                    <button onclick="toggleDarkMode()" title="Toggle Dark Mode">🌙</button>
                    <button onclick="quickCreateFolder()" title="Create Folder">📁</button>
                    <button onclick="quickCreateNote()" title="Create Note">📝</button>
                    <button onclick="quickCreateTask()" title="Create Task">✅</button>
                    <button onclick="quickCreateSmartFolder()" title="Create Smart Folder">💎</button>
                    <button onclick="quickCreateTemplate()" title="Create Template">📦</button>
                    <button onclick="showSettings()" title="Settings">⚙️</button>
                    <button onclick="logout()" title="Logout">🚪</button>
                `;
            }
        }

        // Tagging functionality now imported from tags.js
        let searchTimeoutId = null;

        // showTagModal now imported from tags.js
        
        // hideTagModal now imported from tags.js

        // loadCurrentNodeTags now imported from tags.js

        function renderCurrentTags() {
            const container = document.getElementById('currentTagsList');
            
            if (currentNodeTags.length === 0) {
                container.innerHTML = '<div style="color: #8e8e93; font-style: italic;">No tags yet</div>';
                return;
            }
            
            container.innerHTML = currentNodeTags.map(tag => `
                <span class="tag-chip">
                    ${escapeHtml(tag.name)}
                    <button class="tag-chip-remove" onclick="removeTag('${tag.id}')" title="Remove tag">×</button>
                </span>
            `).join('');
        }


        function renderTagSuggestions(suggestions, query) {
            const container = document.getElementById('tagSuggestions');
            
            // Filter out already attached tags
            const currentTagIds = new Set(currentNodeTags.map(t => t.id));
            const filteredSuggestions = suggestions.filter(tag => !currentTagIds.has(tag.id));
            
            let html = '';
            
            // Add existing matching tags
            filteredSuggestions.forEach(tag => {
                html += `
                    <div class="tag-suggestion" onclick="addExistingTag('${tag.id}', '${escapeHtml(tag.name)}')">
                        <span>${escapeHtml(tag.name)}</span>
                        <span style="color: #8e8e93; font-size: 14px;">Add</span>
                    </div>
                `;
            });
            
            // Add "create new" option if query doesn't match any existing tags exactly
            const exactMatch = suggestions.find(tag => tag.name.toLowerCase() === query.toLowerCase());
            if (!exactMatch && query.length > 0) {
                html += `
                    <div class="tag-suggestion create-new" onclick="createAndAddTag('${escapeHtml(query)}')">
                        <span>Create "${escapeHtml(query)}"</span>
                        <span style="font-size: 14px;">New</span>
                    </div>
                `;
            }
            
            if (html) {
                container.innerHTML = html;
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        }

        async function addExistingTag(tagId, tagName) {
            if (!currentTagModalNodeId) return;
            
            try {
                const response = await fetch(`${API_BASE}/nodes/${currentTagModalNodeId}/tags/${tagId}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (response.ok) {
                    // Add to current tags list
                    currentNodeTags.push({ id: tagId, name: tagName });
                    renderCurrentTags();
                    
                    // Clear search
                    document.getElementById('tagSearchInput').value = '';
                    document.getElementById('tagSuggestions').style.display = 'none';
                    
                    // Refresh smart folders since tag was added to node
                    refreshAllSmartFolders();
                } else {
                    console.error('Failed to add tag');
                }
            } catch (error) {
                console.error('Error adding tag:', error);
            }
        }

        async function createAndAddTag(tagName) {
            if (!currentTagModalNodeId || !tagName.trim()) return;
            
            try {
                // Create the tag first
                const createResponse = await fetch(`${API_BASE}/tags/simple?name=${encodeURIComponent(tagName)}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (createResponse.ok) {
                    const newTag = await createResponse.json();
                    
                    // Add the tag to the node
                    const attachResponse = await fetch(`${API_BASE}/nodes/${currentTagModalNodeId}/tags/${newTag.id}`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });
                    
                    if (attachResponse.ok) {
                        // Add to current tags list
                        currentNodeTags.push({
                            id: newTag.id,
                            name: newTag.name,
                            description: newTag.description,
                            color: newTag.color
                        });
                        renderCurrentTags();
                        
                        // Clear search
                        document.getElementById('tagSearchInput').value = '';
                        document.getElementById('tagSuggestions').style.display = 'none';
                        
                        // Refresh smart folders since new tag was created and added to node
                        refreshAllSmartFolders();
                    } else {
                        console.error('Failed to attach tag to node');
                    }
                } else {
                    console.error('Failed to create tag');
                }
            } catch (error) {
                console.error('Error creating and adding tag:', error);
            }
        }


        function addTagFromInput() {
            const query = document.getElementById('tagSearchInput').value.trim();
            if (query.length > 0) {
                createAndAddTag(query);
            }
        }

        function handleTagSearchKeydown(event) {
            const suggestionsContainer = document.getElementById('tagSuggestions');
            const suggestions = suggestionsContainer.querySelectorAll('.tag-suggestion');
            const query = document.getElementById('tagSearchInput').value.trim();
            
            if (event.key === 'Enter') {
                event.preventDefault();
                
                // If there are suggestions visible, activate the first one
                if (suggestions.length > 0) {
                    suggestions[0].click();
                } else if (query.length > 0) {
                    // No suggestions but there's a query - create new tag
                    addTagFromInput();
                }
            } else if (event.key === 'Escape') {
                hideTagModal();
            }
        }

        // Close modal when clicking outside
        // Commented out - tagModal is now created dynamically by tagging.js
        // document.getElementById('tagModal').addEventListener('click', function(event) {
        //     if (event.target === this) {
        //         hideTagModal();
        //     }
        // });
        
        // Smart Folder Rules View Functions
        let currentSmartFolderRulesId = null;
        
        function openSmartFolderRulesView(nodeId) {
            const node = nodes[nodeId];
            if (!node || node.node_type !== 'smart_folder') return;
            
            currentSmartFolderRulesId = nodeId;
            
            // Update rules view content
            document.getElementById('smartFolderRulesViewTitle').textContent = node.title;
            
            // Render rules content
            renderSmartFolderRules(node);
            
            // Show the rules view
            document.getElementById('mainApp').classList.add('hidden');
            document.getElementById('smartFolderRulesView').classList.remove('hidden');
        }
        
        function closeSmartFolderRulesView() {
            document.getElementById('smartFolderRulesView').classList.add('hidden');
            document.getElementById('mainApp').classList.remove('hidden');
            currentSmartFolderRulesId = null;
        }
        
        function renderSmartFolderRules(node) {
            console.log('renderSmartFolderRules called with node:', node); // Debug log
            const container = document.getElementById('smartFolderRulesViewContent');
            const rules = node.smart_folder_data?.rules || { conditions: [], logic: 'AND' };
            console.log('Extracted rules for display:', rules); // Debug log
            
            let html = '<div class="smart-folder-rules-display">';
            
            // Show logic type
            html += `<div class="rules-overview">
                <h3>Filter Logic: <span style="color: #007AFF;">${rules.logic}</span></h3>
                <p style="color: #666; margin-bottom: 20px;">
                    ${rules.logic === 'AND' ? 'Items must match ALL conditions below' : 'Items must match ANY condition below'}
                </p>
            </div>`;
            
            if (rules.conditions && rules.conditions.length > 0) {
                html += '<div class="rules-list">';
                rules.conditions.forEach((condition, index) => {
                    html += `<div class="rule-display-item">
                        <div class="rule-number">${index + 1}.</div>
                        <div class="rule-content">
                            <div class="rule-title">${formatRuleTitle(condition)}</div>
                            <div class="rule-description">${formatRuleDescription(condition)}</div>
                        </div>
                    </div>`;
                });
                html += '</div>';
            } else {
                html += '<div class="no-rules">' +
                    '<p style="color: #666; font-style: italic; text-align: center; padding: 40px;">' +
                        'No filter rules defined yet. Click Edit to add rules.' +
                    '</p>' +
                '</div>';
            }
            
            html += '</div>';
            
            // Add some CSS for the display
            html += `
                <style>
                    .smart-folder-rules-display {
                        padding: 20px;
                    }
                    
                    .rules-overview h3 {
                        margin-bottom: 8px;
                        font-size: 18px;
                    }
                    
                    .rule-display-item {
                        display: flex;
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 15px;
                        margin-bottom: 10px;
                    }
                    
                    .rule-number {
                        background: #007AFF;
                        color: white;
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: bold;
                        margin-right: 12px;
                        flex-shrink: 0;
                    }
                    
                    .rule-content {
                        flex: 1;
                    }
                    
                    .rule-title {
                        font-weight: bold;
                        margin-bottom: 4px;
                        color: #333;
                    }
                    
                    .rule-description {
                        color: #666;
                        font-size: 14px;
                    }
                </style>
            `;
            
            container.innerHTML = html;
        }
        
        function formatRuleTitle(condition) {
            const type = condition.type || '';
            const operator = condition.operator || '';
            
            switch (type) {
                case 'node_type':
                    return 'Node Type Filter';
                case 'tag_contains':
                    return 'Tag Filter';
                case 'parent_node':
                    return 'Parent Folder Filter';
                case 'task_status':
                    return 'Task Status Filter';
                case 'task_priority':
                    return 'Task Priority Filter';
                case 'title_contains':
                    return 'Title Search Filter';
                case 'has_children':
                    return 'Children Filter';
                default:
                    return 'Filter Rule';
            }
        }
        
        function formatRuleDescription(condition) {
            const type = condition.type || '';
            const operator = condition.operator || '';
            const values = condition.values || [];
            
            switch (type) {
                case 'node_type':
                    if (operator === 'equals') {
                        return `Show only ${values[0]}s`;
                    } else if (operator === 'in') {
                        return `Show ${values.join(', ')} only`;
                    } else if (operator === 'not_equals') {
                        return `Exclude ${values[0]}s`;
                    }
                    break;
                case 'tag_contains':
                    if (operator === 'any') {
                        return `Has any of these tags: ${values.join(', ')}`;
                    } else if (operator === 'all') {
                        return `Has all of these tags: ${values.join(', ')}`;
                    }
                    break;
                case 'task_status':
                    if (operator === 'equals') {
                        return `Task status is ${values[0]}`;
                    } else if (operator === 'in') {
                        return `Task status is ${values.join(' or ')}`;
                    }
                    break;
                case 'task_priority':
                    if (operator === 'equals') {
                        return `Task priority is ${values[0]}`;
                    } else if (operator === 'in') {
                        return `Task priority is ${values.join(' or ')}`;
                    }
                    break;
                case 'title_contains':
                    if (operator === 'contains') {
                        return `Title contains "${values[0]}"`;
                    } else if (operator === 'equals') {
                        return `Title equals "${values[0]}"`;
                    }
                    break;
                case 'has_children':
                    const hasChildren = values[0] === 'true';
                    return hasChildren ? 'Has child items' : 'Has no child items';
                case 'parent_node':
                    const folderNames = values.map(folderId => {
                        if (folderId === 'null' || folderId === null) {
                            return 'Root level';
                        } else if (folderId === currentRoot) {
                            return 'Current folder';
                        } else {
                            const folder = nodes[folderId];
                            return folder ? folder.title : `Folder ${folderId}`;
                        }
                    });
                    return `Under parent folder: ${folderNames.join(', ')}`;
            }
            
            return 'Custom filter rule';
        }
        
        function editSmartFolderRules() {
            if (!currentSmartFolderRulesId) return;
            
            const node = nodes[currentSmartFolderRulesId];
            if (!node) return;
            
            // Set up the editor
            document.getElementById('smartFolderRulesEditorTitle').value = node.title;
            
            // Render the rules editor interface
            renderRulesEditor(node);
            
            // Show editor, hide view
            document.getElementById('smartFolderRulesView').classList.add('hidden');
            document.getElementById('smartFolderRulesEditor').classList.remove('hidden');
        }
        
        function cancelSmartFolderRulesEdit() {
            // Return to rules view
            document.getElementById('smartFolderRulesEditor').classList.add('hidden');
            document.getElementById('smartFolderRulesView').classList.remove('hidden');
        }
        
        function renderRulesEditor(node) {
            const container = document.getElementById('smartFolderRulesEditorBody');
            const rules = node.smart_folder_data?.rules || { conditions: [], logic: 'AND' };
            
            // Set currentRules to the actual node rules
            currentRules = { 
                conditions: [...(rules.conditions || [])], 
                logic: rules.logic || 'AND' 
            };
            
            let html = `
                <div class="logic-selector">
                    <label for="logicSelect"><strong>Logic Type:</strong></label>
                    <select id="logicSelect" onchange="updateLogic()">
                        <option value="AND" ${rules.logic === 'AND' ? 'selected' : ''}>AND (match all conditions)</option>
                        <option value="OR" ${rules.logic === 'OR' ? 'selected' : ''}>OR (match any condition)</option>
                    </select>
                </div>`;
            
            // Section 1: Parent Folder Selection
            html += `
                <div class="rules-section">
                    <div class="rules-section-title">📁 Parent Folder Filter</div>
                    <div class="section-description">Limit results to items within specific parent folders</div>
                    <div class="rule-builder">
                        <select id="parentFolderSelect">
                            <option value="">Select a parent folder...</option>
                            <option value="current">Current folder only</option>
                            <option value="root">Root level items</option>
                        </select>
                    </div>
                </div>`;
            
            // Section 2: Node Types Filtering
            html += `
                <div class="rules-section">
                    <div class="rules-section-title">📄 Node Types</div>
                    <div class="section-description">Filter by specific node types</div>
                    <div class="rule-builder">
                        <div class="filter-group">
                            <label><strong>Include Node Types:</strong></label>
                            <div class="checkbox-group-vertical">
                                <label><input type="checkbox" value="note" onchange="updateNodeTypeRule()"> Notes</label>
                                <label><input type="checkbox" value="task" onchange="updateNodeTypeRule()"> Tasks</label>
                                <label><input type="checkbox" value="folder" onchange="updateNodeTypeRule()"> Folders</label>
                            </div>
                        </div>
                    </div>
                </div>`;
            
            // Section 3: Task Filtering
            html += `
                <div class="rules-section">
                    <div class="rules-section-title">✓ Task Filters</div>
                    <div class="section-description">Filter tasks by status and priority</div>
                    <div class="rule-builder">
                        <div class="filter-group">
                            <label><strong>Task Status:</strong></label>
                            <div class="checkbox-group-vertical">
                                <label><input type="checkbox" value="pending" onchange="updateTaskStatusRule()"> Pending</label>
                                <label><input type="checkbox" value="in_progress" onchange="updateTaskStatusRule()"> In Progress</label>
                                <label><input type="checkbox" value="completed" onchange="updateTaskStatusRule()"> Completed</label>
                                <label><input type="checkbox" value="cancelled" onchange="updateTaskStatusRule()"> Cancelled</label>
                            </div>
                        </div>
                        <div class="filter-group">
                            <label><strong>Task Priority:</strong></label>
                            <div class="checkbox-group">
                                <label><input type="checkbox" value="low" onchange="updateTaskPriorityRule()"> Low</label>
                                <label><input type="checkbox" value="medium" onchange="updateTaskPriorityRule()"> Medium</label>
                                <label><input type="checkbox" value="high" onchange="updateTaskPriorityRule()"> High</label>
                            </div>
                        </div>
                    </div>
                </div>`;
            
            // Section 4: Tag Filtering
            html += `
                <div class="rules-section">
                    <div class="rules-section-title">🏷️ Tag Filters</div>
                    <div class="section-description">Filter items that have specific tags</div>
                    <div class="rule-builder">
                        <div class="tag-filter-controls">
                            <input type="text" id="tagFilterSearchInput" placeholder="Search for tags..." oninput="searchTagsForFilter()">
                            <div id="tagFilterSuggestions" class="tag-suggestions"></div>
                            <div class="selected-tags" id="selectedTagsForFilter">
                                <div class="no-tags">No tags selected</div>
                            </div>
                            <div class="tag-logic-selector">
                                <label>
                                    <input type="radio" name="tagLogic" value="any" checked> Has ANY of these tags
                                </label>
                                <label>
                                    <input type="radio" name="tagLogic" value="all"> Has ALL of these tags
                                </label>
                            </div>
                        </div>
                    </div>
                </div>`;
            
            // Current Rules Display
            html += `
                <div class="rules-section">
                    <div class="rules-section-title">📋 Current Rules</div>
                    <div id="currentRulesList">`;
            
            if (rules.conditions && rules.conditions.length > 0) {
                rules.conditions.forEach((condition, index) => {
                    html += createCurrentRuleDisplay(condition, index);
                });
            } else {
                html += '<div class="no-rules">No rules defined yet. Use the sections above to add filters.</div>';
            }
            
            html += `</div>
                </div>`;
            
            container.innerHTML = html;
            
            // Populate parent folder dropdown and attach event listener
            populateParentFolderDropdown();
            attachParentFolderListener();
            
            // Initialize current rule states with a small delay to ensure DOM is updated
            setTimeout(() => {
                initializeRuleStates(rules.conditions);
            }, 10);
        }
        
        function populateParentFolderDropdown() {
            const select = document.getElementById('parentFolderSelect');
            if (!select) return;
            
            // Clear all options first
            select.innerHTML = '';
            
            // Add static options
            select.appendChild(createOption('', 'All folders'));
            select.appendChild(createOption('current', 'Current folder only'));
            select.appendChild(createOption('root', 'Root level items'));
            
            // Get all folders from the nodes (exclude smart folders and templates)
            const folders = Object.values(nodes).filter(node => 
                node.node_type !== 'template' && // Exclude templates
                node.node_type !== 'smart_folder' && // Exclude smart folders
                (node.node_type === 'note' && node.note_data && node.note_data.body === 'Container folder')
            );
            
            // Sort folders by title
            folders.sort((a, b) => a.title.localeCompare(b.title));
            
            // Add folder options
            if (folders.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = 'Existing Folders';
                
                folders.forEach(folder => {
                    const indent = '\u00A0'.repeat(getNodeDepth(folder.id) * 4); // Non-breaking spaces
                    const option = createOption(folder.id, indent + folder.title);
                    optgroup.appendChild(option);
                });
                
                select.appendChild(optgroup);
            }
        }
        
        function createOption(value, text) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            return option;
        }
        
        function getNodeDepth(nodeId, visited = new Set()) {
            if (visited.has(nodeId)) return 0; // Prevent infinite loops
            visited.add(nodeId);
            
            const node = nodes[nodeId];
            if (!node || !node.parent_id) return 0;
            
            return 1 + getNodeDepth(node.parent_id, visited);
        }
        
        function attachParentFolderListener() {
            const select = document.getElementById('parentFolderSelect');
            if (select) {
                // Remove any existing listeners
                select.removeEventListener('change', addParentFolderRule);
                // Add the event listener
                select.addEventListener('change', addParentFolderRule);
                console.log('Parent folder listener attached to:', select); // Debug log
            } else {
                console.log('Could not find parentFolderSelect element'); // Debug log
            }
        }
        
        function createRuleEditor(condition, index) {
            return `<div class="rule-item" data-index="${index}">
                <div class="rule-description">
                    ${formatRuleDescription(condition)}
                </div>
                <button class="remove-rule-btn" onclick="removeRule(${index})">Remove</button>
            </div>`;
        }
        
        function updateLogic() {
            // Logic update will be handled in save function
        }
        
        function addNewRule() {
            // For now, add a simple placeholder rule
            const rulesList = document.getElementById('rulesList');
            const currentRulesCount = rulesList.children.length;
            
            const newRule = {
                type: 'node_type',
                operator: 'equals',
                values: ['task']
            };
            
            const ruleHtml = createRuleEditor(newRule, currentRulesCount);
            rulesList.insertAdjacentHTML('beforeend', ruleHtml);
        }
        
        function removeRule(index) {
            const ruleItem = document.querySelector(`[data-index="${index}"]`);
            if (ruleItem) {
                ruleItem.remove();
                // Re-index remaining rules
                updateRuleIndices();
            }
        }
        
        function updateRuleIndices() {
            const ruleItems = document.querySelectorAll('#rulesList .rule-item');
            ruleItems.forEach((item, newIndex) => {
                item.setAttribute('data-index', newIndex);
                const removeBtn = item.querySelector('.remove-rule-btn');
                removeBtn.setAttribute('onclick', `removeRule(${newIndex})`);
            });
        }
        
        // Enhanced rule editor functions
        let currentRules = { conditions: [], logic: 'AND' };
        let selectedTagsForFilter = [];
        let searchTagsTimeout = null;
        
        async function createCurrentRuleDisplay(condition, index) {
            return await window.templateSystem.loadAndRender('smartfolders/rule-item.html', {
                index: index,
                ruleDescription: formatRuleDescription(condition)
            });
        }
        
        function initializeRuleStates(conditions) {
            currentRules.conditions = [...(conditions || [])];
            
            // Initialize logic dropdown
            const logicSelect = document.getElementById('logicSelect');
            if (logicSelect && currentRules.logic) {
                logicSelect.value = currentRules.logic;
            }
            
            // Initialize checkboxes based on existing rules
            conditions?.forEach(condition => {
                if (condition.type === 'task_status') {
                    condition.values?.forEach(status => {
                        const checkbox = document.querySelector(`input[type="checkbox"][value="${status}"]`);
                        if (checkbox && checkbox.onchange.toString().includes('updateTaskStatusRule')) {
                            checkbox.checked = true;
                        }
                    });
                } else if (condition.type === 'node_type') {
                    condition.values?.forEach(nodeType => {
                        const checkbox = document.querySelector(`input[type="checkbox"][value="${nodeType}"]`);
                        if (checkbox && checkbox.onchange.toString().includes('updateNodeTypeRule')) {
                            checkbox.checked = true;
                        }
                    });
                } else if (condition.type === 'task_priority') {
                    condition.values?.forEach(priority => {
                        const checkbox = document.querySelector(`input[type="checkbox"][value="${priority}"]`);
                        if (checkbox && checkbox.onchange.toString().includes('updateTaskPriorityRule')) {
                            checkbox.checked = true;
                        }
                    });
                } else if (condition.type === 'tag_contains') {
                    // Initialize selected tags
                    selectedTagsForFilter = condition.values?.map(tagId => ({ id: tagId, name: `Tag ${tagId}` })) || [];
                    renderSelectedTagsForFilter();
                    
                    // Set tag logic radio
                    const radioValue = condition.operator === 'all' ? 'all' : 'any';
                    const radio = document.querySelector(`input[name="tagLogic"][value="${radioValue}"]`);
                    if (radio) radio.checked = true;
                } else if (condition.type === 'parent_node') {
                    // Initialize parent folder dropdown
                    const select = document.getElementById('parentFolderSelect');
                    if (select && condition.values && condition.values.length > 0) {
                        const parentValue = condition.values[0];
                        if (parentValue) {
                            select.value = parentValue;
                        }
                    }
                }
            });
        }
        
        function addParentFolderRule() {
            const select = document.getElementById('parentFolderSelect');
            const value = select.value;
            console.log('Parent folder selected:', value); // Debug log
            
            // Remove existing parent folder rules
            currentRules.conditions = currentRules.conditions.filter(c => c.type !== 'parent_node');
            
            // If empty value selected, it means "All folders" - no parent filter needed
            if (!value) {
                updateCurrentRulesDisplay();
                return;
            }
            
            if (value === 'current' && currentRoot) {
                currentRules.conditions.push({
                    type: 'parent_node',
                    operator: 'equals',
                    values: [currentRoot]
                });
            } else if (value === 'root') {
                currentRules.conditions.push({
                    type: 'parent_node',
                    operator: 'equals',
                    values: ['null'] // Root level (string for API)
                });
            } else {
                // Regular folder ID
                currentRules.conditions.push({
                    type: 'parent_node',
                    operator: 'equals',
                    values: [value]
                });
            }
            
            console.log('Current rules after adding parent folder:', currentRules); // Debug log
            updateCurrentRulesDisplay();
            // Keep the selection visible instead of resetting
            // select.value = '';
        }
        
        function updateNodeTypeRule() {
            console.log('updateNodeTypeRule called'); // Debug log
            const checkedBoxes = document.querySelectorAll('input[type="checkbox"][onchange*="updateNodeTypeRule"]:checked');
            console.log('Found checked node type boxes:', checkedBoxes.length); // Debug log
            const selectedTypes = Array.from(checkedBoxes).map(cb => cb.value);
            console.log('Selected node types:', selectedTypes); // Debug log
            
            // Remove existing node type rules
            currentRules.conditions = currentRules.conditions.filter(c => c.type !== 'node_type');
            
            // If one or more types are selected
            if (selectedTypes.length > 0) {
                const operator = selectedTypes.length === 1 ? 'equals' : 'in';
                const newRule = {
                    type: 'node_type',
                    operator: operator,
                    values: selectedTypes
                };
                console.log('Adding new node type rule:', newRule); // Debug log
                currentRules.conditions.push(newRule);
            }
            
            console.log('Current rules after node type update:', currentRules); // Debug log
            updateCurrentRulesDisplay();
        }
        
        function updateTaskStatusRule() {
            console.log('updateTaskStatusRule called'); // Debug log
            const checkedBoxes = document.querySelectorAll('input[type="checkbox"][onchange*="updateTaskStatusRule"]:checked');
            console.log('Found checked boxes:', checkedBoxes.length); // Debug log
            const selectedStatuses = Array.from(checkedBoxes).map(cb => cb.value);
            console.log('Selected statuses:', selectedStatuses); // Debug log
            
            // Remove existing task status rules
            currentRules.conditions = currentRules.conditions.filter(c => c.type !== 'task_status');
            
            // If one or more statuses are selected
            if (selectedStatuses.length > 0) {
                const operator = selectedStatuses.length === 1 ? 'equals' : 'in';
                const newRule = {
                    type: 'task_status',
                    operator: operator,
                    values: selectedStatuses
                };
                console.log('Adding new task status rule:', newRule); // Debug log
                currentRules.conditions.push(newRule);
            }
            
            console.log('Current rules after update:', currentRules); // Debug log
            updateCurrentRulesDisplay();
        }
        
        function updateTaskPriorityRule() {
            const checkboxes = document.querySelectorAll('input[type="checkbox"][onchange*="updateTaskPriorityRule"]');
            const selectedPriorities = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            
            // Remove existing task priority rules
            currentRules.conditions = currentRules.conditions.filter(c => c.type !== 'task_priority');
            
            if (selectedPriorities.length > 0) {
                currentRules.conditions.push({
                    type: 'task_priority',
                    operator: selectedPriorities.length === 1 ? 'equals' : 'in',
                    values: selectedPriorities
                });
            }
            
            updateCurrentRulesDisplay();
        }
        
        function searchTagsForFilter() {
            const query = document.getElementById('tagFilterSearchInput').value.trim();
            
            if (searchTagsTimeout) {
                clearTimeout(searchTagsTimeout);
            }
            
            searchTagsTimeout = setTimeout(async () => {
                if (query.length === 0) {
                    document.getElementById('tagFilterSuggestions').style.display = 'none';
                    return;
                }
                
                try {
                    const response = await fetch(`${API_BASE}/tags/search?q=${encodeURIComponent(query)}&limit=10`, {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });
                    
                    if (response.ok) {
                        const suggestions = await response.json();
                        renderTagFilterSuggestions(suggestions);
                    }
                } catch (error) {
                    console.error('Error searching tags for filter:', error);
                }
            }, 300);
        }
        
        function renderTagFilterSuggestions(suggestions) {
            const container = document.getElementById('tagFilterSuggestions');
            const selectedTagIds = new Set(selectedTagsForFilter.map(t => t.id));
            
            const filteredSuggestions = suggestions.filter(tag => !selectedTagIds.has(tag.id));
            
            if (filteredSuggestions.length > 0) {
                container.innerHTML = filteredSuggestions.map(tag => `
                    <div class="tag-suggestion" onclick="addTagToFilter('${tag.id}', '${escapeHtml(tag.name)}')">
                        <span>${escapeHtml(tag.name)}</span>
                        <span style="color: #007AFF; font-size: 12px;">Add</span>
                    </div>
                `).join('');
                container.style.display = 'block';
            } else {
                container.style.display = 'none';
            }
        }
        
        function addTagToFilter(tagId, tagName) {
            selectedTagsForFilter.push({ id: tagId, name: tagName });
            renderSelectedTagsForFilter();
            updateTagFilterRule();
            
            // Clear search
            document.getElementById('tagFilterSearchInput').value = '';
            document.getElementById('tagFilterSuggestions').style.display = 'none';
        }
        
        function removeTagFromFilter(tagId) {
            selectedTagsForFilter = selectedTagsForFilter.filter(tag => tag.id !== tagId);
            renderSelectedTagsForFilter();
            updateTagFilterRule();
        }
        
        function renderSelectedTagsForFilter() {
            const container = document.getElementById('selectedTagsForFilter');
            
            if (selectedTagsForFilter.length === 0) {
                window.templateSystem.loadAndRender('smartfolders/no-tags-selected.html')
                    .then(html => container.innerHTML = html);
                return;
            }
            
            container.innerHTML = selectedTagsForFilter.map(tag => `
                <span class="tag-chip">
                    ${escapeHtml(tag.name)}
                    <button class="tag-chip-remove" onclick="removeTagFromFilter('${tag.id}')" title="Remove tag">×</button>
                </span>
            `).join('');
        }
        
        function updateTagFilterRule() {
            // Remove existing tag rules
            currentRules.conditions = currentRules.conditions.filter(c => c.type !== 'tag_contains');
            
            if (selectedTagsForFilter.length > 0) {
                const tagLogic = document.querySelector('input[name="tagLogic"]:checked')?.value || 'any';
                
                currentRules.conditions.push({
                    type: 'tag_contains',
                    operator: tagLogic,
                    values: selectedTagsForFilter.map(tag => tag.id)
                });
            }
            
            updateCurrentRulesDisplay();
        }
        
        async function updateCurrentRulesDisplay() {
            const container = document.getElementById('currentRulesList');
            console.log('Updating rules display, conditions:', currentRules.conditions); // Debug log
            console.log('Container element:', container); // Debug log
            
            if (!container) {
                console.error('currentRulesList container not found!');
                return;
            }
            
            if (currentRules.conditions.length === 0) {
                container.innerHTML = await window.templateSystem.loadAndRender('smartfolders/no-rules-defined.html');
                return;
            }
            
            const rulesHTMLArray = await Promise.all(
                currentRules.conditions.map((condition, index) => 
                    createCurrentRuleDisplay(condition, index)
                )
            );
            const rulesHTML = rulesHTMLArray.join('');
            
            console.log('Setting rules HTML:', rulesHTML); // Debug log
            container.innerHTML = rulesHTML;
        }
        
        function removeCurrentRule(index) {
            const removedCondition = currentRules.conditions[index]; // Get condition before removing
            currentRules.conditions.splice(index, 1);
            updateCurrentRulesDisplay();
            
            // Update UI elements to reflect removal
            if (removedCondition?.type === 'task_status') {
                // Uncheck task status checkboxes
                document.querySelectorAll('input[type="checkbox"][onchange*="updateTaskStatusRule"]')
                    .forEach(cb => cb.checked = false);
            } else if (removedCondition?.type === 'task_priority') {
                // Uncheck task priority checkboxes
                document.querySelectorAll('input[type="checkbox"][onchange*="updateTaskPriorityRule"]')
                    .forEach(cb => cb.checked = false);
            } else if (removedCondition?.type === 'node_type') {
                // Uncheck node type checkboxes
                document.querySelectorAll('input[type="checkbox"][onchange*="updateNodeTypeRule"]')
                    .forEach(cb => cb.checked = false);
            } else if (removedCondition?.type === 'tag_contains') {
                selectedTagsForFilter = [];
                renderSelectedTagsForFilter();
            }
        }
        
        async function saveSmartFolderRules() {
            if (!currentSmartFolderRulesId) return;
            
            const title = document.getElementById('smartFolderRulesEditorTitle').value.trim();
            if (!title) {
                alert('Smart folder name is required');
                return;
            }
            
            // Get the current logic selection
            const logic = document.getElementById('logicSelect').value;
            currentRules.logic = logic;
            
            console.log('Saving smart folder rules:', currentRules); // Debug log
            
            try {
                // Update the smart folder with new rules using SmartFolderUpdate schema
                const response = await fetch(`${API_BASE}/nodes/${currentSmartFolderRulesId}`, {
                    method: 'PUT',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        title: title,
                        smart_folder_data: {
                            rules: currentRules,
                            auto_refresh: true,
                            description: `Smart folder: ${title}`
                        }
                    })
                });
                
                console.log('Save response status:', response.status); // Debug log
                
                if (response.ok) {
                    const updatedNode = await response.json();
                    console.log('Updated node received:', updatedNode); // Debug log
                    nodes[currentSmartFolderRulesId] = updatedNode;
                    
                    // Return to rules view
                    cancelSmartFolderRulesEdit();
                    
                    // Update the view title and re-render rules
                    document.getElementById('smartFolderRulesViewTitle').textContent = title;
                    console.log('Calling renderSmartFolderRules with:', updatedNode); // Debug log
                    renderSmartFolderRules(updatedNode);
                    
                    // Refresh smart folder contents with new rules
                    await refreshSmartFolderContents(currentSmartFolderRulesId);
                    
                    // Re-render the tree if needed
                    renderTree();
                } else {
                    const errorText = await response.text();
                    console.error('Save failed with status:', response.status, 'Error:', errorText);
                    alert(`Failed to save smart folder rules: ${errorText}`);
                }
            } catch (error) {
                console.error('Error saving smart folder rules:', error);
                alert('Error saving smart folder rules');
            }
        }

        // Chat functions now imported from chat.js

        // Make functions globally available for onclick handlers
        // login, logout, toggleDarkMode, backToMain now bound in main.js
        window.showSettings = showSettings;
        window.toggleExpand = toggleExpand;
        window.handleNodeClick = handleNodeClick;
        window.handleFolderIconClick = handleFolderIconClick;
        window.handleFocusTitleClick = handleFocusTitleClick;
        window.navigateToParent = navigateToParent;
        // Make functions available to HTML onclick handlers
        // login, logout now bound in main.js
        window.setAddType = setAddType;
        window.createNode = createNode;
        window.toggleAddForm = toggleAddForm;
        window.quickCreateTask = quickCreateTask;
        window.quickCreateNote = quickCreateNote;
        window.quickCreateFolder = quickCreateFolder;
        window.quickCreateSmartFolder = quickCreateSmartFolder;
        window.quickCreateTemplate = quickCreateTemplate;
        window.toggleTaskComplete = toggleTaskComplete;
        window.editNote = editNote;
        window.saveNote = saveNote;
        window.cancelNoteEdit = cancelNoteEdit;
        window.deleteCurrentNode = deleteCurrentNode;
        window.editFocusedNodeTitle = editFocusedNodeTitle;
        window.exitFocusMode = exitFocusMode;
        // Commented out - these are now handled by tagging.js
        // window.showTagModal = showTagModal;
        // window.hideTagModal = hideTagModal;
        // window.searchTags = searchTags;
        // Commented out - these are now handled by tagging.js
        // window.addExistingTag = addExistingTag;
        // window.addTagFromInput = addTagFromInput;
        // window.removeTag = removeTag;
        // window.handleTagSearchKeydown = handleTagSearchKeydown;
        window.editSmartFolderRules = editSmartFolderRules;
        window.saveSmartFolderRules = saveSmartFolderRules;
        window.cancelSmartFolderRulesEdit = cancelSmartFolderRulesEdit;
        window.addNewRule = addNewRule;
        window.removeRule = removeRule;
        window.removeCurrentRule = removeCurrentRule;
        window.updateTaskStatusRule = updateTaskStatusRule;
        window.updateTaskPriorityRule = updateTaskPriorityRule;
        window.updateNodeTypeRule = updateNodeTypeRule;
        window.updateTagFilterRule = updateTagFilterRule;
        window.updateLogic = updateLogic;
        window.searchTagsForFilter = searchTagsForFilter;
        window.addTagToFilter = addTagToFilter;
        window.removeTagFromFilter = removeTagFromFilter;
        window.toggleFloatingChat = toggleFloatingChat;
        window.closeFloatingChat = closeFloatingChat;
        window.sendChatMessage = sendChatMessage;
        window.handleChatKeyPress = handleChatKeyPress;
        window.updateHeaderButtonsFromMobileApp = updateHeaderButtons;
