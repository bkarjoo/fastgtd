# Smart Folder Rules JSON Schema

## Overview
Smart folder rules are stored as JSON in the database. This document defines the exact structure and conventions.

## Root Structure
```json
{
  "logic": "AND" | "OR",
  "conditions": [...]
}
```

### Fields:
- **logic** (required): String enum ["AND", "OR"]
  - AND: All conditions must match
  - OR: At least one condition must match
- **conditions** (required): Array of condition objects

## Condition Structure
```json
{
  "type": "<condition_type>",
  "operator": "<operator>",
  "values": [...]
}
```

### Fields:
- **type** (required): String identifying what field to filter on
- **operator** (required): String defining the comparison operation
- **values** (required): Array of values to compare against (can be empty for some operators)

## Condition Types and Their Operators

### 1. node_type
Filters by node type (task, note, folder, smart_folder)
```json
{
  "type": "node_type",
  "operator": "in" | "not_in",
  "values": ["task", "note", "folder", "smart_folder"]
}
```

### 2. task_status
Filters tasks by status (only applies to task nodes)
```json
{
  "type": "task_status",
  "operator": "in" | "not_in",
  "values": ["todo", "in_progress", "done", "dropped"]
}
```

### 3. task_priority
Filters tasks by priority (only applies to task nodes)
```json
{
  "type": "task_priority",
  "operator": "in" | "not_in",
  "values": ["low", "medium", "high", "urgent"]
}
```

### 4. title_contains
Filters by title text
```json
{
  "type": "title_contains",
  "operator": "contains" | "not_contains" | "equals" | "starts_with" | "ends_with",
  "values": ["search text"]
}
```

### 5. due_date
Filters tasks by due date (only applies to task nodes)
```json
{
  "type": "due_date",
  "operator": "before" | "after" | "on" | "between" | "is_null" | "is_not_null",
  "values": ["2024-01-15"] // ISO date format, or ["2024-01-15", "2024-01-20"] for between
}
```

### 6. earliest_start
Filters tasks by earliest start date (only applies to task nodes)
```json
{
  "type": "earliest_start",
  "operator": "before" | "after" | "on" | "between" | "is_null" | "is_not_null",
  "values": ["2024-01-15"] // ISO date format, or ["2024-01-15", "2024-01-20"] for between
}
```

### 7. tag_contains
Filters by tags
```json
{
  "type": "tag_contains",
  "operator": "any" | "all" | "none",
  "values": ["tag_uuid_1", "tag_uuid_2"] // Array of tag UUIDs
}
```

### 8. parent_node
Filters by parent node
```json
{
  "type": "parent_node",
  "operator": "equals" | "in" | "not_equals" | "not_in",
  "values": ["parent_uuid"] // Single UUID or array for "in" operator
}
```

### 9. has_children
Filters nodes by whether they have children
```json
{
  "type": "has_children",
  "operator": "equals",
  "values": ["true"] // or ["false"]
}
```

## Complete Examples

### Example 1: All high-priority incomplete tasks
```json
{
  "logic": "AND",
  "conditions": [
    {
      "type": "node_type",
      "operator": "in",
      "values": ["task"]
    },
    {
      "type": "task_priority",
      "operator": "in",
      "values": ["high", "urgent"]
    },
    {
      "type": "task_status",
      "operator": "in",
      "values": ["todo", "in_progress"]
    }
  ]
}
```

### Example 2: Tasks due this week OR overdue
```json
{
  "logic": "OR",
  "conditions": [
    {
      "type": "due_date",
      "operator": "between",
      "values": ["2024-01-15", "2024-01-22"]
    },
    {
      "type": "due_date",
      "operator": "before",
      "values": ["2024-01-15"]
    }
  ]
}
```

### Example 3: Notes with specific tags
```json
{
  "logic": "AND",
  "conditions": [
    {
      "type": "node_type",
      "operator": "in",
      "values": ["note"]
    },
    {
      "type": "tag_contains",
      "operator": "any",
      "values": ["550e8400-e29b-41d4-a716-446655440000", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
    }
  ]
}
```

### Example 4: Empty smart folder (no results)
```json
{
  "logic": "AND",
  "conditions": []
}
```

## Validation Rules

1. **Root object** must have both `logic` and `conditions` fields
2. **logic** must be exactly "AND" or "OR" (case-sensitive)
3. **conditions** must be an array (can be empty)
4. Each **condition** must have `type`, `operator`, and `values` fields
5. **values** must always be an array, even for single values
6. **operator** must be valid for the given `type`
7. Date values must be in ISO format (YYYY-MM-DD)
8. UUIDs must be valid UUID strings

## Backend Implementation Notes

The backend (`SmartFolderRulesEngine`) translates these JSON rules into SQLAlchemy queries:
- Each condition type maps to specific database fields
- AND logic uses `and_()` to combine conditions
- OR logic uses `or_()` to combine conditions
- Task-specific conditions automatically filter for node_type='task'
- Invalid conditions are ignored or return validation errors

## Frontend Implementation Notes

The frontend should:
1. Parse the rules JSON when loading a smart folder
2. Generate valid JSON when saving rules
3. Validate the structure before sending to API
4. Handle empty conditions array as "no filter" (returns no results)