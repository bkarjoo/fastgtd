# Phase 2 Execution Plan - Core Function Extraction

Based on analysis of `mobile-app.js` (3,311 lines), this plan breaks down Phase 2 into specific, manageable steps.

## Current State Analysis
- **File size**: 3,311 lines of monolithic code  
- **Key areas identified**: Auth, UI state, settings, nodes, drag-drop, chat
- **Global state**: API_BASE, authToken, nodes, expandedNodes, currentRoot, addType, currentPage

## Step-by-Step Execution Plan

### Step 1: Create `state.js` (Foundation) ✅ COMPLETED
**Extract lines**: 1-6, 76 and related global variables
```javascript
// Target functions/variables:
- API_BASE = 'http://100.68.227.105:8003'
- authToken management  
- nodes = {}
- expandedNodes = new Set()
- currentRoot = null
- addType = 'task'
- currentPage = 'main'
```
**Status**: ✅ COMPLETED & TESTED - Fully integrated state.js with mobile-app.js
**What was done**: 
- Created centralized state.js with proper ES6 exports
- Replaced all global variables in mobile-app.js with imports
- Fixed readonly property errors with setter functions  
- Resolved naming conflicts (setAddType)
- Added window bindings for HTML onclick handlers
**Testing**: ✅ App loads, login works, node tree displays, state.js visible in DevTools
**Actual effort**: 45 minutes (including debugging integration issues)  
**Risk level**: Medium (required significant debugging of ES6 module integration)

### Step 2: Extract to `auth.js` ✅ COMPLETED
**Extract lines**: 36-73 (login, logout functions)
```javascript
// Target functions:
- login() (lines 36-65)
- logout() (lines 67-73)
- showMainApp() (lines 26-29)  
- showLoginScreen() (lines 31-34)
```
**Status**: ✅ COMPLETED & TESTED - Authentication module successfully extracted
**What was done**:
- Created `static/js/auth.js` with all 4 authentication functions
- Added imports from `state.js` for API_BASE, setAuthToken, clearState
- Updated `mobile-app.js` to import auth functions instead of defining them
- Removed ~40 lines of auth code from mobile-app.js
**Testing**: ✅ App loads, login works, logout works, auth.js visible in DevTools Sources  
**Actual effort**: 25 minutes  
**Risk level**: Low (cleaner than expected, good module separation)

### Step 3: Extract to `ui.js` ✅ COMPLETED
**Extract lines**: 18-24, 78-279, 1989+ (UI concerns)
```javascript
// Target functions:
- initDarkMode() (lines 18-24)
- toggleDarkMode() (lines 1989+)
- getNodeIcon() (lines 98-112) - utility function
- backToMain() (lines 60-63)
- updateNavigation() (lines 187-201)
```
**Status**: ✅ COMPLETED & TESTED - Core UI module successfully extracted
**What was done**:
- Created `static/js/ui.js` with 5 core UI functions
- Added imports from `state.js` for currentPage, setCurrentPage, nodes
- Updated `mobile-app.js` to import UI functions instead of defining them
- Removed ~50 lines of UI code from mobile-app.js
- Added window.toggleDarkMode binding for HTML onclick handlers
**Testing**: ✅ App loads normally, dark mode toggle works, ui.js visible in DevTools Sources
**Actual effort**: 30 minutes  
**Risk level**: Low (clean extraction, skipped complex settings functions)

### Step 4: Update `main.js` - Global Function Bindings ✅ COMPLETED
```javascript
// Add to main.js:
window.login = login;
window.logout = logout;
window.toggleDarkMode = toggleDarkMode;
window.backToMain = backToMain;
```
**Status**: ✅ COMPLETED & TESTED - Centralized global bindings successfully implemented
**What was done**:
- Updated main.js to import from auth.js and ui.js modules
- Added centralized global function bindings in main.js for extracted functions
- Removed duplicate window bindings from mobile-app.js (cleaned 2 sections)
- Added clear documentation comments explaining new organization
**Testing**: ✅ Login works, logout works, dark mode toggle works, app functions identically
**Actual effort**: 15 minutes
**Risk level**: Low (clean implementation, all tests passed)

### Step 5: Extract to `settings.js` ✅ COMPLETED
**Extract lines**: 162-254 (settings-related functions)
```javascript
// Target functions:
- showSettings() - settings page display
- editSettings() - settings edit mode  
- populateDefaultNodeSelect() (lines 162-184)
- loadCurrentDefault() (lines 186-203)
- saveSettings() (lines 204-228)
- loadCurrentDefaultForDisplay() (lines 230-254)
```
**Status**: ✅ COMPLETED & TESTED - Settings module successfully extracted
**What was done**:
- Created `static/js/settings.js` with all settings functions
- Added imports from `state.js` and `ui.js` for dependencies
- Updated `mobile-app.js` to import settings functions instead of defining them
- Added window bindings in main.js for HTML onclick handlers
- Removed ~95 lines of settings code from mobile-app.js
**Testing**: ✅ Settings page loads, edit mode works, save works (minor network timeout on repeat saves)
**Actual effort**: 35 minutes  
**Risk level**: Low (isolated functionality, minor client-side timeout issue noted)

## Testing Strategy
1. **After each step**: Test login/logout flow
2. **After Step 3**: Test dark mode toggle  
3. **After Step 4**: Test all inline click handlers
4. **After Step 5**: Test settings page functionality

## Rollback Plan
- Keep original `mobile-app.js` as `mobile-app.js.backup`
- Each step is in git commits for easy revert
- Test functionality after each extraction

## Success Criteria
- ✅ App loads and functions identically 
- ✅ All onclick handlers work
- ✅ Login/logout flow intact
- ✅ Dark mode toggle works
- ✅ Settings page functional
- ✅ No console errors
- ✅ Code is more modular and maintainable

## Time Estimate: 2.5-3 hours total
**Actual Total Time**: 2.5 hours (150 minutes actual vs 180 minutes estimated) - **50 minutes ahead of schedule!**

## Progress Summary

### Completed Steps:
- ✅ **Step 1: Create `state.js`** - COMPLETED & TESTED (45 min actual vs 30 min estimated)
- ✅ **Step 2: Extract `auth.js`** - COMPLETED & TESTED (25 min actual vs 45 min estimated)
- ✅ **Step 3: Extract `ui.js`** - COMPLETED & TESTED (30 min actual vs 60 min estimated)
- ✅ **Step 4: Update `main.js`** - COMPLETED & TESTED (15 min actual vs 20 min estimated)
- ✅ **Step 5: Extract `settings.js`** - COMPLETED & TESTED (35 min actual vs 45 min estimated)

### Remaining Steps:
- ✅ **All steps completed!** Phase 2 is 100% complete

## Overall Project Phases

- **Phase 1**: Set up Vite build system and modular structure scaffolding ✅ COMPLETE
- **Phase 2**: Extract core functionality (auth, UI, settings, state management) ✅ COMPLETE  
- **Phase 3**: Extract node CRUD, drag-drop, and chat logic ⏳ PENDING
- **Phase 4**: Replace inline HTML with template partials ⏳ PENDING