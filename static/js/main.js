// Entry point for the mobile app
// Phase 2: Central hub for module imports and global function bindings

// Import URL safety module first (patches fetch globally)
import './url-safety.js?v=1735576231';

// Import extracted modules
import { login, logout } from './auth.js?v=1735576231';
import { toggleDarkMode, backToMain } from './ui.js?v=1735576231';
import { showSettings, editSettings, saveSettings } from './settings.js?v=1735576231';
import { toggleExpand, handleNodeClick, handleFolderIconClick, exitFocusMode, toggleTaskComplete, createNode, deleteCurrentNode, editFocusedNodeTitle, handleFocusTitleClick } from './nodes.js?v=1735576231';
import { toggleAddForm, quickCreateFolder, quickCreateNote, quickCreateTask, quickCreateSmartFolder, quickCreateTemplate, useCurrentTemplate, loadParentOptions, setAddType } from './creation.js?v=1735576231';
import { openNoteView, closeNoteView, editNote, cancelNoteEdit, saveNote } from './notes.js?v=1735576231';
import { initTouchDragAndDrop, handleDragStart, handleDragOver, handleDrop, handleDragEnd, handleDropOut, moveNode, moveNodeOut } from './dragdrop.js?v=1735576231';
import { showTagModal, hideTagModal, loadCurrentNodeTags } from './tags.js?v=1735576231';
import { loadSmartFolderContents, refreshSmartFolderContents, refreshAllSmartFolders, loadSmartFolderContentsFocus } from './smartfolders.js?v=1735576231';
import { toggleFloatingChat, closeFloatingChat, sendChatMessage, sendToAI, updateAIContext, handleChatKeyPress } from './chat.js?v=1735576231';
import { initializeNavigation, navigateToFocus, navigateToDetails, navigateToEdit, navigateBack, navigateWithUnsavedCheck, saveNodeChanges, deleteNodeFromDetails } from './navigation.js?v=1735576231';

// Import legacy code (still contains most functionality)
import '../mobile-app.js?v=1735576231';

// Global function bindings for HTML onclick handlers
// These functions are available to all HTML onclick attributes
window.login = login;
window.logout = logout;
window.toggleDarkMode = toggleDarkMode;
window.backToMain = backToMain;
window.showSettings = showSettings;
window.editSettings = editSettings;
window.saveSettings = saveSettings;

// Phase 3 Step 1: Node function bindings
window.toggleExpand = toggleExpand;
window.handleNodeClick = handleNodeClick;
window.handleFolderIconClick = handleFolderIconClick;
window.exitFocusMode = exitFocusMode;
window.toggleTaskComplete = toggleTaskComplete;
window.createNode = createNode;
window.deleteCurrentNode = deleteCurrentNode;
window.editFocusedNodeTitle = editFocusedNodeTitle;
window.handleFocusTitleClick = handleFocusTitleClick;

// Phase 3 Step 2: Creation function bindings
window.toggleAddForm = toggleAddForm;
window.quickCreateFolder = quickCreateFolder;
window.quickCreateNote = quickCreateNote;
window.quickCreateTask = quickCreateTask;
window.quickCreateSmartFolder = quickCreateSmartFolder;
window.quickCreateTemplate = quickCreateTemplate;
window.useCurrentTemplate = useCurrentTemplate;
window.loadParentOptions = loadParentOptions;
window.setAddType = setAddType;

// Phase 3 Step 3: Note function bindings
window.openNoteView = openNoteView;
window.closeNoteView = closeNoteView;
window.editNote = editNote;
window.cancelNoteEdit = cancelNoteEdit;
window.saveNote = saveNote;

// Phase 3 Step 4: Drag and Drop function bindings
window.initTouchDragAndDrop = initTouchDragAndDrop;
window.handleDragStart = handleDragStart;
window.handleDragOver = handleDragOver;
window.handleDrop = handleDrop;
window.handleDragEnd = handleDragEnd;
window.handleDropOut = handleDropOut;
window.moveNode = moveNode;
window.moveNodeOut = moveNodeOut;

// Phase 3 Step 5: Tag Management function bindings (minimal)
window.showTagModal = showTagModal;
window.hideTagModal = hideTagModal;
window.loadCurrentNodeTags = loadCurrentNodeTags;

// Phase 3 Step 6: Smart Folder function bindings (basic loading)
window.loadSmartFolderContents = loadSmartFolderContents;
window.refreshSmartFolderContents = refreshSmartFolderContents;
window.refreshAllSmartFolders = refreshAllSmartFolders;
window.loadSmartFolderContentsFocus = loadSmartFolderContentsFocus;

// Phase 3 Step 7: Chat/AI function bindings
window.toggleFloatingChat = toggleFloatingChat;
window.closeFloatingChat = closeFloatingChat;
window.sendChatMessage = sendChatMessage;
window.sendToAI = sendToAI;
window.updateAIContext = updateAIContext;
window.handleChatKeyPress = handleChatKeyPress;

// Phase 4: Navigation system function bindings
window.navigateToFocus = navigateToFocus;
window.navigateToDetails = navigateToDetails;
window.navigateToEdit = navigateToEdit;
window.navigateBack = navigateBack;
window.navigateWithUnsavedCheck = navigateWithUnsavedCheck;
window.saveNodeChanges = saveNodeChanges;
window.deleteNodeFromDetails = deleteNodeFromDetails;

// Initialize navigation system after DOM loads
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
});
