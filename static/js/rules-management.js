// Rules Management Module
import { API_BASE, authToken, setCurrentRoot } from './state.js';
import { renderTree } from './nodes.js';

// Show all rules in a list view
export async function showAllRules() {
    try {
        // For now, skip the API call since it doesn't exist yet
        // TODO: Uncomment when API is implemented
        /*
        const response = await fetch(`${API_BASE}/rules`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) {
            console.error('Failed to load rules');
            return;
        }
        
        const allRules = await response.json();
        */
        
        // Use mock data for now
        const allRules = null;
        
        // Create a virtual "Rules" view by setting currentRoot to a special value
        setCurrentRoot('__rules__');
        
        // Render the rules list in the tree container
        const container = document.getElementById('nodeTree');
        if (!container) return;
        
        let html = '';
        
        // Add a header
        html += `
            <div class="focus-header">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div onclick="exitRulesView(); event.stopPropagation();" style="cursor: pointer; font-size: 18px; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.1);" title="Back to settings">◀</div>
                        <div style="font-size: 16px; display: flex; align-items: center;">📋</div>
                        <div class="focus-title" style="padding: 4px 8px;">Smart Folder Rules</div>
                    </div>
                    <div style="display: flex; gap: 8px; margin-left: auto;">
                        <button onclick="createNewRule(); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; padding: 4px 12px; background: #007aff; color: white; border: none; border-radius: 6px; font-size: 14px; cursor: pointer;" title="Create new rule">+ New Rule</button>
                    </div>
                </div>
            </div>
        `;
        
        // List all rules (for now, use mock data since we don't have the backend yet)
        const mockRules = [
            {
                id: 'rule1',
                name: 'High Priority Tasks',
                description: 'All high and urgent priority tasks',
                logic: 'AND',
                conditions: [
                    { type: 'node_type', operator: 'in', values: ['task'] },
                    { type: 'task_priority', operator: 'in', values: ['high', 'urgent'] }
                ]
            },
            {
                id: 'rule2',
                name: 'Due This Week',
                description: 'Tasks due in the next 7 days',
                logic: 'AND',
                conditions: [
                    { type: 'node_type', operator: 'in', values: ['task'] },
                    { type: 'due_date', operator: 'between', values: ['today', 'today+7'] }
                ]
            },
            {
                id: 'rule3',
                name: 'All Notes',
                description: 'Show all note items',
                logic: 'AND',
                conditions: [
                    { type: 'node_type', operator: 'in', values: ['note'] }
                ]
            }
        ];
        
        if (mockRules.length === 0) {
            html += '<div style="text-align: center; padding: 20px; color: #666;">No rules yet. Create your first rule!</div>';
        } else {
            html += '<div class="rule-list-container" style="padding: 10px;">';
            mockRules.forEach(rule => {
                const conditionsText = `${rule.conditions.length} condition${rule.conditions.length !== 1 ? 's' : ''}`;
                html += `
                    <div class="node-item rule-list-item" onclick="editRule('${rule.id}')" style="display: flex; align-items: center; padding: 12px; border-radius: 8px; margin-bottom: 8px; cursor: pointer;">
                        <div style="flex: 1;">
                            <div class="rule-name" style="font-size: 16px; font-weight: 500; margin-bottom: 4px;">${rule.name}</div>
                            <div class="rule-info" style="display: flex; gap: 12px; font-size: 14px; color: #86868b;">
                                <span>${rule.description || ''}</span>
                                <span>•</span>
                                <span>Logic: ${rule.logic}</span>
                                <span>•</span>
                                <span>${conditionsText}</span>
                            </div>
                        </div>
                        <button onclick="deleteRule('${rule.id}'); event.stopPropagation();" style="display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: #ff3b30; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; flex-shrink: 0;" title="Delete rule">×</button>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        container.innerHTML = html;
        
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

// Exit rules view and go back to settings
export function exitRulesView() {
    // Go back to settings page
    if (window.showSettings) {
        window.showSettings();
    } else {
        // Fallback to root if showSettings is not available
        setCurrentRoot(null);
        renderTree();
    }
}

// Create a new rule
export async function createNewRule() {
    // For now, just show an alert
    alert('Rule editor will open here (to be implemented)');
    // TODO: Open rule editor modal
}

// Edit an existing rule
export async function editRule(ruleId) {
    // For now, just show an alert
    alert(`Edit rule ${ruleId} (to be implemented)`);
    // TODO: Open rule editor modal with existing rule data
}

// Delete a rule
export async function deleteRule(ruleId) {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    
    try {
        // TODO: Implement actual API call when backend is ready
        /*
        const response = await fetch(`${API_BASE}/rules/${ruleId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            // Refresh the rules view
            showAllRules();
        } else {
            alert('Failed to delete rule');
        }
        */
        
        // For now, just refresh the view
        showAllRules();
    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Error deleting rule');
    }
}

// Make functions available globally
window.showAllRules = showAllRules;
window.exitRulesView = exitRulesView;
window.createNewRule = createNewRule;
window.editRule = editRule;
window.deleteRule = deleteRule;