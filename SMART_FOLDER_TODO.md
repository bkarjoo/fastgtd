# Smart Folder Rules System - TODO

## ✅ Completed Features
- [x] Basic condition types (node_type, task_status, task_priority, title_contains)
- [x] Existing Filter references (saved_filter type)
- [x] AND/OR logic at root level
- [x] Saving rules to database
- [x] JSON ↔ Form bidirectional conversion
- [x] Test environment for rule development
- [x] Rule management (create, save, load, delete)
- [x] Dark mode support for test output

## 🚧 Backend Implementation Required

### High Priority
- [ ] **saved_filter (Existing Filter) backend support**
  - Implement in `SmartFolderRulesEngine` 
  - Recursively apply referenced smart folder's rules
  - Prevent circular references at runtime

### Date Filtering
- [ ] **due_date filtering backend**
  - Operators: before, after, on, between, is_null, is_not_null
  - Handle timezone considerations
  
- [ ] **earliest_start filtering backend**
  - Same operators as due_date
  - Filter on task_data.earliest_start_at field

### Other Filters
- [ ] **tag_contains backend**
  - Operators: any, all, none
  - Join with node_tags table
  
- [ ] **parent_node backend**
  - Operators: equals, in, not_equals, not_in
  - Filter by parent_id field
  
- [ ] **has_children backend**
  - Check if node has any children
  - Boolean true/false

## 🎨 Frontend UI Components

### Date Pickers
- [ ] **Date picker for single date selection**
  - For operators: before, after, on
  
- [ ] **Date range picker**
  - For operator: between
  - Start and end date inputs

### Selection UIs
- [ ] **Tag selector modal**
  - Show available tags
  - Multi-select with checkboxes
  - Search/filter tags
  - Return tag IDs not names
  
- [ ] **Parent node selector**
  - Tree view or dropdown
  - Show folder hierarchy
  - Single or multi-select based on operator

### Simple Controls
- [ ] **has_children toggle**
  - Simple checkbox or toggle for true/false

## 🔧 System Features

### Preview & Testing
- [ ] **Connect Preview Results button**
  - Call backend preview endpoint
  - Display matching nodes
  - Show count and sample items
  
- [ ] **Implement /nodes/smart_folder/preview endpoint**
  - Accept rules JSON
  - Return filtered results without saving

### Validation
- [ ] **Frontend validation**
  - Require at least one condition (or explicitly allow empty)
  - Validate date formats
  - Ensure required values are provided
  
- [ ] **Backend validation**
  - Validate rules JSON schema
  - Check for circular references in saved_filter
  - Return meaningful error messages

### Import/Export
- [ ] **Export rules as JSON**
  - Download button for rule configuration
  
- [ ] **Import rules from JSON**
  - Upload or paste JSON rules
  - Validate before applying

## 📊 User Experience

### Feedback
- [ ] **Empty results handling**
  - Clear message when smart folder has no matches
  - Suggest why (e.g., "No tasks match the selected priority")
  
- [ ] **Loading states**
  - Show spinner while filtering
  - Indicate when results are being fetched

### Rule Templates
- [ ] **Pre-built rule templates**
  - "Overdue tasks"
  - "This week's priorities"
  - "Untagged items"
  - "Empty folders"
  
- [ ] **Save as template**
  - Allow users to save rules as reusable templates

## 🐛 Bug Fixes & Edge Cases

- [ ] **Fix duplicate smart folders in dropdown**
  - After saving, duplicates may appear
  
- [ ] **Handle deleted referenced filters**
  - What happens when saved_filter references deleted smart folder?
  
- [ ] **Performance optimization**
  - Cache smart folder results
  - Efficient recursive rule evaluation

## 📝 Documentation

- [ ] **User guide for rule creation**
- [ ] **Examples of complex rule combinations**
- [ ] **API documentation for rule endpoints**
- [ ] **Schema validation documentation**

## Priority Order

1. **Backend saved_filter implementation** - Critical for "Existing Filter" feature
2. **Date filtering backend** - Common use case
3. **Tag selector UI** - Better than typing UUIDs
4. **Preview functionality** - Test before save
5. **Validation** - Prevent invalid rules
6. **Other condition types** - Complete the feature set