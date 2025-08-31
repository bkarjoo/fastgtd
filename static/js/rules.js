/**
 * Rules Management Module
 * Handles CRUD operations for rules via the Rules API
 */

const RULES_API = '/rules';

// Cache for loaded rules
let rulesCache = {};

/**
 * Load all rules accessible to the current user
 */
async function loadRules(includePublic = true, includeSystem = true) {
    try {
        const params = new URLSearchParams();
        if (includePublic) params.append('include_public', 'true');
        if (includeSystem) params.append('include_system', 'true');
        
        const response = await fetch(`${RULES_API}/?${params}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load rules: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Update cache
        rulesCache = {};
        data.rules.forEach(rule => {
            rulesCache[rule.id] = rule;
        });
        
        return data.rules;
    } catch (error) {
        console.error('Error loading rules:', error);
        return [];
    }
}

/**
 * Get a specific rule by ID
 */
async function getRule(ruleId) {
    // Check cache first
    if (rulesCache[ruleId]) {
        return rulesCache[ruleId];
    }
    
    try {
        const response = await fetch(`${RULES_API}/${ruleId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to get rule: ${response.statusText}`);
        }
        
        const rule = await response.json();
        rulesCache[ruleId] = rule;
        return rule;
    } catch (error) {
        console.error('Error getting rule:', error);
        return null;
    }
}

/**
 * Create a new rule
 */
async function createRule(ruleData) {
    try {
        const response = await fetch(`${RULES_API}/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(ruleData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to create rule: ${response.statusText}`);
        }
        
        const rule = await response.json();
        rulesCache[rule.id] = rule;
        return rule;
    } catch (error) {
        console.error('Error creating rule:', error);
        throw error;
    }
}

/**
 * Update an existing rule
 */
async function updateRule(ruleId, updates) {
    try {
        const response = await fetch(`${RULES_API}/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to update rule: ${response.statusText}`);
        }
        
        const rule = await response.json();
        rulesCache[rule.id] = rule;
        return rule;
    } catch (error) {
        console.error('Error updating rule:', error);
        throw error;
    }
}

/**
 * Delete a rule
 */
async function deleteRule(ruleId) {
    try {
        const response = await fetch(`${RULES_API}/${ruleId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to delete rule: ${response.statusText}`);
        }
        
        delete rulesCache[ruleId];
        return true;
    } catch (error) {
        console.error('Error deleting rule:', error);
        throw error;
    }
}

/**
 * Duplicate an existing rule
 */
async function duplicateRule(ruleId, newName = null) {
    try {
        const params = new URLSearchParams();
        if (newName) params.append('new_name', newName);
        
        const response = await fetch(`${RULES_API}/${ruleId}/duplicate?${params}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Failed to duplicate rule: ${response.statusText}`);
        }
        
        const rule = await response.json();
        rulesCache[rule.id] = rule;
        return rule;
    } catch (error) {
        console.error('Error duplicating rule:', error);
        throw error;
    }
}

/**
 * Create or update a rule from the current smart folder editor state
 */
async function saveRuleFromEditor(ruleName, ruleDescription = null, isPublic = false) {
    // Collect the current rules from the editor
    const ruleData = collectSmartFolderRules();
    
    const rulePayload = {
        name: ruleName,
        description: ruleDescription,
        rule_data: ruleData,
        is_public: isPublic
    };
    
    return await createRule(rulePayload);
}

/**
 * Update smart folder to use a rule
 */
async function updateSmartFolderRule(smartFolderId, ruleId) {
    try {
        // Get the current smart folder
        const response = await fetch(`${API_BASE}/nodes/${smartFolderId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to get smart folder: ${response.statusText}`);
        }
        
        const smartFolder = await response.json();
        
        // Update the smart folder with the rule_id
        const updateData = {
            ...smartFolder,
            smart_folder_data: {
                ...smartFolder.smart_folder_data,
                rule_id: ruleId,
                // Keep rules for backward compatibility during transition
                rules: smartFolder.smart_folder_data?.rules
            }
        };
        
        const updateResponse = await fetch(`${API_BASE}/nodes/${smartFolderId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!updateResponse.ok) {
            throw new Error(`Failed to update smart folder: ${updateResponse.statusText}`);
        }
        
        return await updateResponse.json();
    } catch (error) {
        console.error('Error updating smart folder rule:', error);
        throw error;
    }
}

/**
 * Show rule selector dialog
 */
function showRuleSelector(callback) {
    loadRules().then(rules => {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Select a Rule</h3>
                <div class="rules-list">
                    ${rules.map(rule => `
                        <div class="rule-item" data-rule-id="${rule.id}">
                            <div class="rule-name">${rule.name}</div>
                            ${rule.description ? `<div class="rule-description">${rule.description}</div>` : ''}
                            <div class="rule-meta">
                                ${rule.is_public ? '<span class="badge">Public</span>' : ''}
                                ${rule.is_system ? '<span class="badge">System</span>' : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="modal-actions">
                    <button onclick="this.closest('.modal').remove()">Cancel</button>
                </div>
            </div>
        `;
        
        // Add click handlers
        modal.querySelectorAll('.rule-item').forEach(item => {
            item.addEventListener('click', () => {
                const ruleId = item.dataset.ruleId;
                const rule = rulesCache[ruleId];
                if (callback) callback(rule);
                modal.remove();
            });
        });
        
        document.body.appendChild(modal);
    });
}

/**
 * Create a new rule from current editor and link to smart folder
 */
async function createAndLinkRule(smartFolderId, ruleName) {
    try {
        // Create the rule
        const rule = await saveRuleFromEditor(ruleName);
        
        // Link it to the smart folder
        await updateSmartFolderRule(smartFolderId, rule.id);
        
        return rule;
    } catch (error) {
        console.error('Error creating and linking rule:', error);
        throw error;
    }
}

// Export functions for use in other modules
window.RulesAPI = {
    loadRules,
    getRule,
    createRule,
    updateRule,
    deleteRule,
    duplicateRule,
    saveRuleFromEditor,
    updateSmartFolderRule,
    showRuleSelector,
    createAndLinkRule
};