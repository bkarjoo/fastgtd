# SmartFolder Rules Migration Guide

## Overview

FastGTD is transitioning from inline JSON rules stored directly on SmartFolder nodes to a more robust system using standalone `Rule` entities. This change provides better rule management, reusability, and organization.

## Why Migrate?

### Old System (Deprecated)
```python
# SmartFolder with inline rules
{
    "id": "...",
    "title": "High Priority Tasks",
    "rules": {
        "conditions": [
            {"field": "priority", "operator": "equals", "value": "high"}
        ],
        "logic": "AND"
    }
}
```

**Problems:**
- Rules cannot be reused across multiple SmartFolders
- No versioning or history of rule changes
- Difficult to manage and organize complex rules
- No way to share rules between users

### New System (Recommended)
```python
# Rule entity
{
    "id": "rule-123",
    "name": "High Priority Filter",
    "rule_data": {
        "conditions": [
            {"field": "priority", "operator": "equals", "value": "high"}
        ],
        "logic": "AND"
    },
    "is_public": false
}

# SmartFolder references the rule
{
    "id": "...",
    "title": "High Priority Tasks",
    "rule_id": "rule-123"  # Reference to Rule entity
}
```

**Benefits:**
- Rules are reusable across multiple SmartFolders
- Rules can be versioned and managed independently
- Rules can be shared (public rules) or kept private
- Better organization and discoverability
- Cleaner API design

## Migration Status

### Current State (Jan 2025)

Both systems are supported for backward compatibility:

- ✅ **Legacy `rules` field**: Still works but shows deprecation warnings
- ✅ **New `rule_id` field**: Recommended for all new SmartFolders
- ✅ **Automatic migration tools**: Available in `app/services/smart_folder_migration.py`

### Deprecation Timeline

- **Phase 1 (Current)**: Both systems supported with warnings
- **Phase 2 (Future)**: Legacy system marked for removal
- **Phase 3 (TBD)**: Legacy `rules` field removed

## How to Migrate

### Option 1: Using the API (Recommended)

#### Step 1: Create a Rule from existing SmartFolder

```bash
# Get your SmartFolder
curl -H "Authorization: Bearer $TOKEN" \
  ${API_BASE}/nodes/{smart_folder_id}

# Note the "rules" field content

# Create a Rule entity
curl -X POST ${API_BASE}/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Filter Rule",
    "description": "Migrated from SmartFolder",
    "rule_data": {
      "conditions": [...],
      "logic": "AND"
    }
  }'

# Response includes rule_id
```

#### Step 2: Update SmartFolder to use Rule

```bash
# Update the SmartFolder
curl -X PUT ${API_BASE}/nodes/{smart_folder_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "smart_folder_data": {
      "rule_id": "newly-created-rule-id",
      "auto_refresh": true
    }
  }'
```

### Option 2: Using Migration Utilities

```python
from app.services.smart_folder_migration import (
    migrate_smart_folder_rules_to_rule_entity,
    migrate_all_legacy_smart_folders
)
from app.db.session import async_session_maker

async def migrate_my_folders():
    async with async_session_maker() as session:
        # Migrate a specific SmartFolder
        smart_folder = await session.get(SmartFolder, folder_id)
        rule = await migrate_smart_folder_rules_to_rule_entity(
            smart_folder,
            session,
            rule_name="Custom Rule Name"
        )
        await session.commit()

        # Or migrate all legacy SmartFolders at once
        count = await migrate_all_legacy_smart_folders(session)
        print(f"Migrated {count} SmartFolders")
```

### Option 3: Creating New SmartFolders with Rules

When creating new SmartFolders, use `rule_id` from the start:

```bash
# First, create the Rule
curl -X POST ${API_BASE}/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Urgent Tasks",
    "rule_data": {
      "conditions": [
        {"field": "priority", "operator": "equals", "value": "high"},
        {"field": "status", "operator": "equals", "value": "todo"}
      ],
      "logic": "AND"
    }
  }'

# Then create SmartFolder with rule_id
curl -X POST ${API_BASE}/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "node_type": "smart_folder",
    "title": "Urgent Tasks",
    "smart_folder_data": {
      "rule_id": "rule-id-from-above",
      "auto_refresh": true
    }
  }'
```

## Migration Utilities Reference

### `get_effective_rule_data(smart_folder, session)`

Get the active rule data for a SmartFolder, preferring `rule_id` over legacy `rules`:

```python
from app.services.smart_folder_migration import get_effective_rule_data

rule_data = await get_effective_rule_data(smart_folder, session)
# Returns the rule_data dict from Rule entity or falls back to legacy rules
```

### `migrate_smart_folder_rules_to_rule_entity(smart_folder, session, rule_name=None)`

Convert a SmartFolder's legacy rules to a Rule entity:

```python
from app.services.smart_folder_migration import migrate_smart_folder_rules_to_rule_entity

rule = await migrate_smart_folder_rules_to_rule_entity(
    smart_folder,
    session,
    rule_name="My Custom Rule"  # Optional
)
# Creates a Rule entity and updates smart_folder.rule_id
```

### `migrate_all_legacy_smart_folders(session)`

Migrate all SmartFolders that have legacy rules but no rule_id:

```python
from app.services.smart_folder_migration import migrate_all_legacy_smart_folders

count = await migrate_all_legacy_smart_folders(session)
print(f"Migrated {count} SmartFolders")
```

### `ensure_smart_folder_has_rule_entity(smart_folder, session)`

Ensure a SmartFolder has a Rule entity, creating one if needed:

```python
from app.services.smart_folder_migration import ensure_smart_folder_has_rule_entity

rule = await ensure_smart_folder_has_rule_entity(smart_folder, session)
# Returns existing Rule or creates a new one from legacy rules
```

## API Changes

### Creating SmartFolders

**Old way (deprecated but still works):**
```json
{
  "node_type": "smart_folder",
  "title": "My Folder",
  "smart_folder_data": {
    "rules": {
      "conditions": [...],
      "logic": "AND"
    }
  }
}
```

**New way (recommended):**
```json
{
  "node_type": "smart_folder",
  "title": "My Folder",
  "smart_folder_data": {
    "rule_id": "uuid-of-rule-entity"
  }
}
```

### Response Format

SmartFolder responses now include both fields during transition:

```json
{
  "id": "...",
  "node_type": "smart_folder",
  "title": "My Folder",
  "smart_folder_data": {
    "rule_id": "uuid-of-rule",  // New field
    "rules": {...},              // Legacy field (may be null if using rule_id)
    "auto_refresh": true,
    "description": "..."
  }
}
```

## Best Practices

### 1. Create Reusable Rules

Instead of creating a new rule for each SmartFolder, create shared rules:

```python
# Create a rule once
high_priority_rule = Rule(
    name="High Priority Filter",
    rule_data={"conditions": [...], "logic": "AND"}
)

# Use it in multiple SmartFolders
folder1.rule_id = high_priority_rule.id
folder2.rule_id = high_priority_rule.id
```

### 2. Use Descriptive Rule Names

```python
# Good
Rule(name="Overdue High Priority Tasks", ...)

# Bad
Rule(name="Rule 1", ...)
```

### 3. Add Descriptions

```python
Rule(
    name="Sprint Planning",
    description="Shows unscheduled high priority tasks for sprint planning",
    rule_data={...}
)
```

### 4. Consider Public Rules

Make commonly-used rules public so they're available to all users:

```python
Rule(
    name="Today's Tasks",
    description="Tasks due today",
    rule_data={...},
    is_public=True  # Available to all users
)
```

## Troubleshooting

### Deprecation Warnings

If you see warnings like:
```
DeprecationWarning: The 'rules' field is deprecated. Use 'rule_id' to reference a Rule entity instead.
```

**Solution**: Update your code to use `rule_id` instead of `rules`.

### Rule Not Found Error

If you get `404: Rule not found or not accessible`:

**Check:**
1. The rule_id exists in the database
2. The rule is owned by you OR is marked as `is_public=True` OR is a system rule
3. The UUID format is correct

### Legacy Rules Still Showing

Even after migration, legacy `rules` may still appear in responses for backward compatibility. This is expected during the transition period.

## Need Help?

- Check the API documentation: `${API_BASE}/docs`
- Review migration utilities: `app/services/smart_folder_migration.py`
- Run tests: `pytest tests/api/test_nodes.py -k smart_folder`

## Future Enhancements

Planned improvements to the Rule system:

- Rule versioning and history
- Rule composition (rules that reference other rules)
- Rule templates and presets
- Rule performance analytics
- Bulk rule operations