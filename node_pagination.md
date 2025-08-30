# Node Pagination Implementation Plan

## Overview
This document outlines the implementation of consistent pagination flow across all node types in FastGTD. Each node type will follow the same 3-page pattern with consistent navigation behavior.

## Node Types
- Node (generic)
- Task
- Note
- Smart Folder
- Template

## Page Flow Architecture

### 1. Focus Page (Default View)
**Purpose**: Primary content view when clicking a node from the tree
**Navigation**: 
- Entry: Click node from tree/parent view
- Exit: Back button → returns to parent node
- Forward: Click node title → Detail Render Page

**Common Elements**:
- Node title (clickable → Detail Render Page)
- Back button
- Content area (specific to node type)
- Action buttons (specific to node type)

### 2. Detail Render Page (Read-Only Details)
**Purpose**: Display detailed information in read-only format
**Navigation**:
- Entry: Click node title from Focus Page
- Exit: Back button → Focus Page
- Forward: Edit button → Detail Edit Page

**Common Elements**:
- Node title/header
- Back button
- Edit button
- Read-only detail fields (specific to node type)
- Metadata display

### 3. Detail Edit Page (Editable Details)
**Purpose**: Edit node details and properties
**Navigation**:
- Entry: Click Edit button from Detail Render Page
- Exit: Back button → Detail Render Page (with confirmation if unsaved changes)
- Save: Save button → Detail Render Page (after successful save)

**Common Elements**:
- Form header
- Back button (with unsaved changes warning)
- Save button
- Cancel button (optional)
- Editable form fields (specific to node type)
- Validation feedback

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create base page components/templates
2. Implement common navigation logic
3. Set up routing structure
4. Create shared UI components (buttons, headers, etc.)

### Phase 2: Node-Specific Implementation
Implement each node type individually in this order:
1. **Node** (generic) - simplest implementation
2. **Note** - basic content editing
3. **Task** - task-specific fields and status
4. **Smart Folder** - folder properties and rules
5. **Template** - template configuration

### Phase 3: Testing & Refinement
Test each node type completely before moving to the next:
- Navigation flow testing
- Data persistence testing
- UI/UX consistency verification

## Technical Considerations

### URL Structure
```
/node/{id}                    # Focus Page
/node/{id}/details           # Detail Render Page  
/node/{id}/edit             # Detail Edit Page

/task/{id}                   # Focus Page
/task/{id}/details          # Detail Render Page
/task/{id}/edit             # Detail Edit Page

# Similar pattern for note, smart-folder, template
```

### State Management
- Track current page in navigation state
- Handle unsaved changes warnings
- Maintain parent-child relationships for back navigation

### Common Components Needed
- `NodeHeader` - consistent header with title and navigation
- `BackButton` - standardized back navigation
- `EditButton` - consistent edit action button
- `SaveButton` - standardized save functionality
- `NavigationGuard` - handle unsaved changes warnings

## Node-Specific Content Plans

### Node (Generic)
- **Focus Page**: Basic node content, child nodes list
- **Detail Render Page**: Node metadata, creation date, parent info
- **Detail Edit Page**: Name, description, basic properties

### Task
- **Focus Page**: Task status, due date, subtasks, notes
- **Detail Render Page**: All task details, priority, tags, history
- **Detail Edit Page**: Task properties, status, dates, assignments

### Note
- **Focus Page**: Note content preview, linked items
- **Detail Render Page**: Full note content, metadata, tags
- **Detail Edit Page**: Note content editor, tags, properties

### Smart Folder
- **Focus Page**: Contained items, folder stats
- **Detail Render Page**: Folder rules, criteria, metadata
- **Detail Edit Page**: Filter rules, folder properties

### Template
- **Focus Page**: Template preview, usage stats
- **Detail Render Page**: Template structure, metadata
- **Detail Edit Page**: Template definition, properties

## Success Criteria
- [ ] Consistent navigation flow across all node types
- [ ] Back button always returns to correct parent context
- [ ] Edit functionality maintains data integrity
- [ ] Unsaved changes are properly handled
- [ ] UI/UX is consistent across all implementations
- [ ] Each node type tested independently before moving to next

## Next Steps
1. Review and approve this plan
2. Begin with Phase 1: Core Infrastructure
3. Implement Node (generic) type first
4. Test thoroughly before proceeding to next node type