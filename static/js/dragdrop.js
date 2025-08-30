// Drag and Drop module - handles both touch and desktop drag & drop functionality
import { API_BASE, authToken, nodes, currentRoot, setCurrentRoot } from './state.js';
import { loadNodes } from './nodes.js';

// Touch drag and drop system for mobile
export function initTouchDragAndDrop() {
    let dragState = {
        isDragging: false,
        dragElement: null,
        originalElement: null,
        startTime: 0,
        startY: 0,
        currentY: 0,
        dragThreshold: 10,
        longPressTime: 600,
        longPressTimer: null,
        dropZone: null,
        scrollContainer: null
    };

    // Add touch event listeners to the node tree container
    function attachTouchListeners() {
        const nodeTree = document.getElementById('nodeTree');
        if (nodeTree) {
            nodeTree.addEventListener('touchstart', handleTouchStart, {passive: false});
            nodeTree.addEventListener('touchmove', handleTouchMove, {passive: false});
            nodeTree.addEventListener('touchend', handleTouchEnd, {passive: false});
        }
    }

    function handleTouchStart(e) {
        const nodeItem = e.target.closest('.node-item');
        if (!nodeItem || !nodeItem.dataset.nodeId) return;

        // Prevent text selection
        // e.preventDefault();
        
        dragState.startTime = Date.now();
        dragState.startY = e.touches[0].clientY;
        dragState.currentY = dragState.startY;
        dragState.originalElement = nodeItem;
        dragState.scrollContainer = document.querySelector('.app-layout');

        // Start long press timer
        dragState.longPressTimer = setTimeout(() => {
            if (!dragState.isDragging) {
                startDrag(nodeItem, e.touches[0]);
            }
        }, dragState.longPressTime);
    }

    function handleTouchMove(e) {
        if (!dragState.originalElement) return;

        dragState.currentY = e.touches[0].clientY;
        const deltaY = Math.abs(dragState.currentY - dragState.startY);

        if (dragState.isDragging) {
            e.preventDefault();
            updateDragPosition(e.touches[0]);
            updateDropTarget(e.touches[0]);
        } else if (deltaY > dragState.dragThreshold) {
            // Movement detected - cancel long press if not already dragging
            clearTimeout(dragState.longPressTimer);
        }
    }

    function handleTouchEnd(e) {
        clearTimeout(dragState.longPressTimer);

        if (dragState.isDragging) {
            e.preventDefault();
            finalizeDrop();
        }

        resetDragState();
    }

    function startDrag(element, touch) {
        dragState.isDragging = true;
        
        // Add haptic feedback if available
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }

        // Create drag clone
        const rect = element.getBoundingClientRect();
        dragState.dragElement = element.cloneNode(true);
        dragState.dragElement.classList.add('dragging-clone');
        
        // Style the clone
        Object.assign(dragState.dragElement.style, {
            position: 'fixed',
            top: rect.top + 'px',
            left: rect.left + 'px',
            width: rect.width + 'px',
            zIndex: '9999',
            opacity: '0.9',
            transform: 'rotate(2deg)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.3)',
            pointerEvents: 'none',
            borderRadius: '8px'
        });

        // Style original element
        dragState.originalElement.style.opacity = '0.3';
        
        document.body.appendChild(dragState.dragElement);

        // Add drag styles to body
        document.body.classList.add('dragging-active');
    }

    function updateDragPosition(touch) {
        if (!dragState.dragElement) return;

        const deltaY = touch.clientY - dragState.startY;
        const rect = dragState.originalElement.getBoundingClientRect();
        
        dragState.dragElement.style.top = (rect.top + deltaY) + 'px';
        dragState.dragElement.style.left = rect.left + 'px';
    }

    function updateDropTarget(touch) {
        // Hide drag element temporarily to get element underneath
        const dragEl = dragState.dragElement;
        dragEl.style.display = 'none';
        
        const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
        const targetNode = elementBelow?.closest('.node-item');
        
        dragEl.style.display = 'block';

        // Clear previous drop indicators
        clearDropIndicators();

        if (targetNode && targetNode !== dragState.originalElement) {
            const rect = targetNode.getBoundingClientRect();
            const relativeY = touch.clientY - rect.top;
            const zone = getDropZone(relativeY, rect.height);
            
            dragState.dropZone = {
                element: targetNode,
                zone: zone
            };

            showDropIndicator(targetNode, zone);
        }
    }

    function getDropZone(relativeY, height) {
        if (relativeY < height * 0.25) return 'above';
        if (relativeY > height * 0.75) return 'below';
        return 'inside';
    }

    function showDropIndicator(element, zone) {
        if (zone === 'above') {
            const indicator = document.createElement('div');
            indicator.className = 'touch-drop-indicator above';
            element.parentNode.insertBefore(indicator, element);
        } else if (zone === 'below') {
            const indicator = document.createElement('div');
            indicator.className = 'touch-drop-indicator below';
            element.parentNode.insertBefore(indicator, element.nextSibling);
        } else {
            element.classList.add('touch-drop-target-inside');
        }
    }

    function clearDropIndicators() {
        document.querySelectorAll('.touch-drop-indicator').forEach(el => el.remove());
        document.querySelectorAll('.touch-drop-target-inside').forEach(el => {
            el.classList.remove('touch-drop-target-inside');
        });
    }

    function finalizeDrop() {
        if (dragState.dropZone) {
            const sourceId = dragState.originalElement.dataset.nodeId;
            const targetId = dragState.dropZone.element.dataset.nodeId;
            const zone = dragState.dropZone.zone;

            if (sourceId && targetId && sourceId !== targetId) {
                moveNode(sourceId, targetId, zone);
            }
        }

        clearDropIndicators();
    }

    function resetDragState() {
        if (dragState.dragElement) {
            dragState.dragElement.remove();
        }
        
        if (dragState.originalElement) {
            dragState.originalElement.style.opacity = '';
        }

        document.body.classList.remove('dragging-active');
        clearDropIndicators();

        dragState = {
            isDragging: false,
            dragElement: null,
            originalElement: null,
            startTime: 0,
            startY: 0,
            currentY: 0,
            dragThreshold: 10,
            longPressTime: 600,
            longPressTimer: null,
            dropZone: null,
            scrollContainer: null
        };
    }

    // Attach listeners initially and reattach when tree updates
    attachTouchListeners();
    
    // Re-attach listeners when tree is updated
    const originalRenderTree = window.renderTree;
    window.renderTree = function() {
        if (originalRenderTree) originalRenderTree();
        setTimeout(attachTouchListeners, 100);
    };
}

// Desktop drag and drop MVC pattern
const DragDropController = {
    model: {
        draggedNodeId: null,
        dropZone: null,
        
        setDraggedNode(nodeId) {
            this.draggedNodeId = nodeId;
        },
        
        setDropZone(zone) {
            this.dropZone = zone;
        },
        
        reset() {
            this.draggedNodeId = null;
            this.dropZone = null;
        },
        
        calculateDropZone(mouseY, elementHeight) {
            if (mouseY < elementHeight * 0.33) return 'above';
            if (mouseY > elementHeight * 0.66) return 'below';
            return 'inside';
        }
    },
    
    view: {
        setDragOpacity(element, opacity) {
            element.style.opacity = opacity;
        },
        
        clearDropIndicators() {
            document.querySelectorAll('.drop-indicator').forEach(el => el.remove());
            document.querySelectorAll('.drop-target-inside').forEach(el => {
                el.classList.remove('drop-target-inside');
            });
        },
        
        showDropIndicator(targetElement, zone) {
            this.clearDropIndicators();
            
            if (zone === 'above') {
                const indicator = document.createElement('div');
                indicator.className = 'drop-indicator above';
                targetElement.parentNode.insertBefore(indicator, targetElement);
            } else if (zone === 'below') {
                const indicator = document.createElement('div');
                indicator.className = 'drop-indicator below';
                targetElement.parentNode.insertBefore(indicator, targetElement.nextSibling);
            } else if (zone === 'inside') {
                targetElement.classList.add('drop-target-inside');
            }
        }
    },
    
    handleDragStart(event) {
        const nodeId = event.currentTarget.dataset.nodeId;
        this.model.setDraggedNode(nodeId);
        event.dataTransfer.effectAllowed = 'move';
        // Needed in many browsers for drop to fire
        event.dataTransfer.setData('text/plain', nodeId);
        this.view.setDragOpacity(event.currentTarget, '0.5');
    },
    
    handleDragOver(event) {
        event.preventDefault();
        const targetElement = event.currentTarget;
        const rect = targetElement.getBoundingClientRect();
        const mouseY = event.clientY - rect.top;
        const height = rect.height;
        
        const zone = this.model.calculateDropZone(mouseY, height);
        this.model.setDropZone(zone);
        this.view.showDropIndicator(targetElement, zone);
        
        event.dataTransfer.dropEffect = 'move';
    },
    
    handleDrop(event) {
        event.preventDefault();
        const targetNodeId = event.currentTarget.dataset.nodeId;
        const sourceNodeId = this.model.draggedNodeId;
        const dropZone = this.model.dropZone;
        
        if (sourceNodeId && targetNodeId && sourceNodeId !== targetNodeId) {
            moveNode(sourceNodeId, targetNodeId, dropZone);
        }
        
        this.view.clearDropIndicators();
    },
    
    handleDragEnd(event) {
        this.view.setDragOpacity(event.currentTarget, '1');
        this.model.reset();
        this.view.clearDropIndicators();
    }
};

// Desktop drag and drop event handlers
export function handleDragStart(event) {
    DragDropController.handleDragStart(event);
}

export function handleDragOver(event) {
    DragDropController.handleDragOver(event);
}

export function handleDrop(event) {
    DragDropController.handleDrop(event);
}

export function handleDragEnd(event) {
    DragDropController.handleDragEnd(event);
}

export function handleDropOut(event) {
    event.preventDefault();
    const sourceNodeId = DragDropController.model.draggedNodeId;
    const targetParentId = event.currentTarget.dataset.nodeId === 'root' ? null : event.currentTarget.dataset.nodeId;
    
    if (sourceNodeId) {
        moveNodeOut(sourceNodeId, targetParentId);
    }
    
    // Clean up visual indicators
    DragDropController.view.clearDropIndicators();
}

// Move node to a different parent
export async function moveNodeOut(sourceId, newParentId) {
    const sourceNode = nodes[sourceId];
    if (!sourceNode) return;
    
    // Calculate a new sort order (put at end of siblings)
    const siblings = Object.values(nodes).filter(n => n.parent_id === newParentId && n.id !== sourceId);
    const maxSortOrder = siblings.reduce((max, node) => Math.max(max, node.sort_order || 0), -1);
    const newSortOrder = maxSortOrder + 1;
    
    // Build payload
    const payload = {
        title: sourceNode.title,
        node_type: sourceNode.node_type,
        parent_id: newParentId,
        sort_order: newSortOrder
    };
    
    // Add type-specific data
    if (sourceNode.node_type === 'task' && sourceNode.task_data) {
        payload.task_data = {
            description: sourceNode.task_data.description || '',
            status: sourceNode.task_data.status || 'todo',
            priority: sourceNode.task_data.priority || 'medium',
            archived: sourceNode.task_data.archived || false,
            due_at: sourceNode.task_data.due_at || null,
            earliest_start_at: sourceNode.task_data.earliest_start_at || null,
            completed_at: sourceNode.task_data.completed_at || null,
            recurrence_rule: sourceNode.task_data.recurrence_rule || null,
            recurrence_anchor: sourceNode.task_data.recurrence_anchor || null
        };
    } else if (sourceNode.node_type === 'note' && sourceNode.note_data) {
        payload.note_data = {
            body: (sourceNode.note_data && sourceNode.note_data.body) || ''
        };
    }
    
    console.log('Moving node out:', {
        sourceId,
        newParentId,
        currentRoot,
        siblings: siblings.map(n => ({id: n.id, title: n.title, sort_order: n.sort_order})),
        maxSortOrder,
        newSortOrder
    });
    console.log('Moving node out payload:', payload);
    
    try {
        const response = await fetch(`${API_BASE}/nodes/${sourceId}`, {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}` 
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            // If we moved to parent level, exit focus mode to see the result
            if (newParentId !== currentRoot) {
                setCurrentRoot(newParentId);
                updateAIContext();
            }
            // Reload data from server to get correct state
            await loadNodes();
        } else {
            const errorData = await response.text();
            console.error('Move node out failed:', response.status, errorData);
            alert(`Failed to move node out: ${response.status}`);
        }
    } catch (error) {
        console.error('Error moving node out:', error);
        alert('Error moving node out');
    }
}

// Move node with drag and drop reordering
export async function moveNode(sourceId, targetId, zone) {
    const sourceNode = nodes[sourceId];
    const targetNode = nodes[targetId];
    
    if (!sourceNode || !targetNode) return;
    
    // Determine the destination parent for ordering purposes
    const newParentId = (zone === 'inside') ? targetId : targetNode.parent_id;

    // Build the desired order of node IDs within the destination parent
    const baseSiblings = Object.values(nodes)
        .filter(n => n.parent_id === newParentId && n.id !== sourceId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

    let insertIndex;
    if (zone === 'inside') {
        insertIndex = baseSiblings.length; // append to end
    } else {
        const targetIndex = baseSiblings.findIndex(n => n.id === targetId);
        insertIndex = (zone === 'above') ? targetIndex : targetIndex + 1;
    }

    const newOrderIds = baseSiblings.map(n => n.id);
    newOrderIds.splice(insertIndex, 0, sourceId);

    // Proceed to move and reorder on server
    try {
        // If parent is changing, move first
        if (sourceNode.parent_id !== newParentId) {
            const moveRes = await fetch(`${API_BASE}/nodes/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    node_id: sourceId,
                    new_parent_id: newParentId,
                    new_sort_order: null
                })
            });
            if (!moveRes.ok) {
                const errText = await moveRes.text();
                throw new Error(`Move failed: ${moveRes.status} ${errText}`);
            }
        }

        // Reorder siblings within the destination parent
        const reorderRes = await fetch(`${API_BASE}/nodes/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ node_ids: newOrderIds })
        });
        if (!reorderRes.ok) {
            const errText = await reorderRes.text();
            throw new Error(`Reorder failed: ${reorderRes.status} ${errText}`);
        }

        // Reload to reflect the new order
        await loadNodes();
    } catch (error) {
        console.error('Error moving/reordering node:', error);
        alert('Error moving node');
    }
}

// These functions will be extracted in later steps
function updateAIContext() { if (typeof window.updateAIContext === 'function') window.updateAIContext(); }