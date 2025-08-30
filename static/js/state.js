// Global application state management
// This module centralizes all shared state variables

// API Configuration
// Auto-detects local vs remote access:
// - Local (localhost/127.0.0.1): Uses http://localhost:8003
// - Remote (Tailscale): Uses http://100.68.227.105:8003
// Server must run with: uvicorn app.main:app --reload --port 8003 --host 0.0.0.0
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
export const API_BASE = isLocal ? 'http://localhost:8003' : 'http://100.68.227.105:8003';

// Authentication state
export let authToken = localStorage.getItem('authToken');
export function setAuthToken(token) {
    authToken = token;
    if (token) {
        localStorage.setItem('authToken', token);
    } else {
        localStorage.removeItem('authToken');
    }
}

// Node tree state
export let nodes = {};
export let expandedNodes = new Set();
export let currentRoot = null;
export let addType = 'task';

// UI state
export let currentPage = 'main'; // 'main' or 'settings'

// Navigation state for 3-page flow
export let navigationStack = []; // Stack of navigation states
export let currentView = 'focus'; // 'focus', 'details', 'edit'
export let currentNodeId = null; // Node being viewed in details/edit

// State management functions
export function setNodes(newNodes) {
    nodes = newNodes;
}

export function setCurrentRoot(rootId) {
    currentRoot = rootId;
}

export function setAddType(type) {
    addType = type;
}

export function setCurrentPage(page) {
    currentPage = page;
}

// Navigation state setters
export function setCurrentView(view) {
    currentView = view;
}

export function setCurrentNodeId(nodeId) {
    currentNodeId = nodeId;
}

export function pushNavigationState(state) {
    navigationStack.push(state);
}

export function popNavigationState() {
    return navigationStack.pop();
}

export function clearNavigationStack() {
    navigationStack = [];
}

// Current note management
export let currentNoteId = null;
export function setCurrentNoteId(noteId) {
    currentNoteId = noteId;
}

export function clearState() {
    nodes = {};
    expandedNodes.clear();
    currentRoot = null;
    setAuthToken(null);
}

// Utility function to safely construct URLs with parent_id parameter
export function buildNodeURL(baseUrl, parentId) {
    // Only include parent_id if it's a valid UUID
    if (!parentId || parentId === 'null' || parentId === '' || parentId === null || parentId === undefined) {
        return baseUrl;
    }
    
    // Basic UUID validation (36 characters with hyphens at positions 8, 13, 18, 23)
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(parentId)) {
        console.warn(`Invalid parent_id provided: ${parentId}. Omitting from URL.`);
        return baseUrl;
    }
    
    return `${baseUrl}?parent_id=${parentId}`;
}