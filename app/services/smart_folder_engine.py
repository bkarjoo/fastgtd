"""Smart folder rules engine for dynamic node filtering"""
from typing import Dict, List, Any, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.node import Node, Task, Note, SmartFolder
from app.models.tag import Tag
from app.models.node_associations import node_tags
from app.models.enums import TaskStatus, TaskPriority


class SmartFolderRulesEngine:
    """Engine for evaluating smart folder rules and generating filtered node queries"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def evaluate_smart_folder(self, smart_folder: SmartFolder, owner_id: UUID) -> List[Node]:
        """Evaluate a smart folder's rules and return matching nodes"""
        rules = smart_folder.rules
        if not rules or not rules.get("conditions"):
            return []
        
        # Build the base query
        query = select(Node).where(
            Node.owner_id == owner_id,
            Node.id != smart_folder.id,  # Exclude the smart folder itself
            Node.node_type != "template"  # Exclude templates from search results
        )
        
        # Apply conditions
        conditions = []
        for condition in rules.get("conditions", []):
            condition_filter = await self._build_condition_filter(condition, owner_id)
            if condition_filter is not None:
                conditions.append(condition_filter)
        
        if conditions:
            # Apply logic (AND/OR)
            logic = rules.get("logic", "AND")
            if logic == "AND":
                query = query.where(and_(*conditions))
            else:  # OR
                query = query.where(or_(*conditions))
        
        # Execute query
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _build_condition_filter(self, condition: Dict[str, Any], owner_id: UUID):
        """Build SQLAlchemy filter from a condition dictionary"""
        condition_type = condition.get("type")
        operator = condition.get("operator")
        values = condition.get("values", [])
        
        if not condition_type or not operator or not values:
            return None
        
        if condition_type == "node_type":
            return self._build_node_type_filter(operator, values)
        
        elif condition_type == "tag_contains":
            return await self._build_tag_filter(operator, values, owner_id)
        
        elif condition_type == "parent_node":
            return self._build_parent_filter(operator, values)
        
        elif condition_type == "task_status":
            return self._build_task_status_filter(operator, values)
        
        elif condition_type == "task_priority":
            return self._build_task_priority_filter(operator, values)
        
        elif condition_type == "title_contains":
            return self._build_title_filter(operator, values)
        
        elif condition_type == "has_children":
            return await self._build_children_filter(operator, values)
            
        elif condition_type == "due_date":
            return self._build_date_filter(operator, values, "due_at")
            
        elif condition_type == "earliest_start":
            return self._build_date_filter(operator, values, "earliest_start_at")
        
        elif condition_type == "saved_filter":
            return await self._build_saved_filter(operator, values, owner_id)
        
        return None
    
    def _build_node_type_filter(self, operator: str, values: List[str]):
        """Build filter for node type conditions"""
        if operator == "equals":
            return Node.node_type == values[0]
        elif operator == "in":
            return Node.node_type.in_(values)
        elif operator == "not_equals":
            return Node.node_type != values[0]
        return None
    
    async def _build_tag_filter(self, operator: str, values: List[str], owner_id: UUID):
        """Build filter for tag-related conditions"""
        # Convert string UUIDs to UUID objects
        try:
            tag_uuids = [UUID(v) for v in values]
        except (ValueError, TypeError):
            return None
        
        if operator == "any":
            # Node has any of the specified tags
            return Node.id.in_(
                select(node_tags.c.node_id).where(
                    node_tags.c.tag_id.in_(tag_uuids)
                )
            )
        elif operator == "all":
            # Node has all of the specified tags
            # This is complex - need to check each tag individually
            subqueries = []
            for tag_uuid in tag_uuids:
                subqueries.append(
                    select(node_tags.c.node_id).where(
                        node_tags.c.tag_id == tag_uuid
                    )
                )
            
            if len(subqueries) == 1:
                return Node.id.in_(subqueries[0])
            else:
                # Node must appear in all subqueries
                base_query = subqueries[0]
                for subquery in subqueries[1:]:
                    base_query = base_query.intersect(subquery)
                return Node.id.in_(base_query)
        
        return None
    
    def _build_parent_filter(self, operator: str, values: List[str]):
        """Build filter for parent node conditions"""
        try:
            if operator == "equals":
                return Node.parent_id == UUID(values[0])
            elif operator == "in":
                parent_uuids = [UUID(v) for v in values]
                return Node.parent_id.in_(parent_uuids)
        except (ValueError, TypeError):
            pass
        return None
    
    def _build_task_status_filter(self, operator: str, values: List[str]):
        """Build filter for task status conditions (only applies to task nodes)"""
        try:
            if operator == "equals":
                status = TaskStatus(values[0])
                return and_(
                    Node.node_type == "task",
                    Node.id.in_(
                        select(Task.id).where(Task.status == status)
                    )
                )
            elif operator == "in":
                statuses = [TaskStatus(v) for v in values]
                return and_(
                    Node.node_type == "task",
                    Node.id.in_(
                        select(Task.id).where(Task.status.in_(statuses))
                    )
                )
        except (ValueError, TypeError):
            pass
        return None
    
    def _build_task_priority_filter(self, operator: str, values: List[str]):
        """Build filter for task priority conditions (only applies to task nodes)"""
        try:
            if operator == "equals":
                priority = TaskPriority(values[0])
                return and_(
                    Node.node_type == "task",
                    Node.id.in_(
                        select(Task.id).where(Task.priority == priority)
                    )
                )
            elif operator == "in":
                priorities = [TaskPriority(v) for v in values]
                return and_(
                    Node.node_type == "task",
                    Node.id.in_(
                        select(Task.id).where(Task.priority.in_(priorities))
                    )
                )
        except (ValueError, TypeError):
            pass
        return None
    
    def _build_title_filter(self, operator: str, values: List[str]):
        """Build filter for title search conditions"""
        if operator == "contains":
            return Node.title.ilike(f"%{values[0]}%")
        elif operator == "equals":
            return Node.title == values[0]
        return None
    
    async def _build_children_filter(self, operator: str, values: List[str]):
        """Build filter for nodes with/without children"""
        if operator == "equals":
            has_children = values[0].lower() in ("true", "1", "yes")
            if has_children:
                # Nodes that have children
                return Node.id.in_(
                    select(Node.parent_id).where(Node.parent_id.is_not(None)).distinct()
                )
            else:
                # Nodes that don't have children
                return Node.id.not_in(
                    select(Node.parent_id).where(Node.parent_id.is_not(None)).distinct()
                )
        return None
    
    async def _build_saved_filter(self, operator: str, values: List[str], owner_id: UUID):
        """Build filter for saved filter (rule reference) conditions"""
        if not values or not values[0]:
            return None
            
        rule_id = values[0]
        
        # Import here to avoid circular imports
        from app.models.rule import Rule
        
        # Get the referenced rule
        rule_query = select(Rule).where(
            Rule.id == rule_id,
            or_(
                Rule.owner_id == owner_id,
                Rule.is_public == True,
                Rule.is_system == True
            )
        )
        
        result = await self.session.execute(rule_query)
        rule = result.scalar_one_or_none()
        
        if not rule or not rule.rule_data:
            return None
        
        # Recursively evaluate the referenced rule's conditions
        conditions = []
        for condition in rule.rule_data.get("conditions", []):
            condition_filter = await self._build_condition_filter(condition, owner_id)
            if condition_filter is not None:
                conditions.append(condition_filter)
        
        if not conditions:
            return None
            
        # Apply the referenced rule's logic
        logic = rule.rule_data.get("logic", "AND")
        if logic == "AND":
            return and_(*conditions)
        else:  # OR
            return or_(*conditions)
    
    async def preview_smart_folder_results(self, rules: Dict[str, Any], owner_id: UUID, limit: int = 10) -> List[Node]:
        """Preview results for smart folder rules without creating the folder"""
        # Create a temporary smart folder object for evaluation
        temp_folder = SmartFolder(
            id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy ID
            owner_id=owner_id,
            title="Preview",
            rules=rules,
            node_type="smart_folder"
        )
        
        results = await self.evaluate_smart_folder(temp_folder, owner_id)
        return results[:limit]  # Limit results for preview
    
    def _build_date_filter(self, operator: str, values: List[str], date_field: str):
        """Build filter for date-based conditions (due_at, earliest_start_at)"""
        from datetime import datetime
        
        # Only apply to task nodes since they have these date fields
        base_condition = and_(
            Node.node_type == "task",
            Node.id.in_(
                select(Task.id)
            )
        )
        
        if operator == "is_null":
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        getattr(Task, date_field).is_(None)
                    )
                )
            )
            
        elif operator == "is_not_null":
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        getattr(Task, date_field).is_not(None)
                    )
                )
            )
        
        if not values or not values[0]:
            return None
            
        try:
            date_value = datetime.fromisoformat(values[0]).replace(tzinfo=None)
            
            if operator == "on":
                # On specific date (comparing just the date part)
                next_day = date_value.replace(hour=23, minute=59, second=59)
                start_day = date_value.replace(hour=0, minute=0, second=0)
                return and_(
                    base_condition,
                    Node.id.in_(
                        select(Task.id).where(
                            and_(
                                getattr(Task, date_field) >= start_day,
                                getattr(Task, date_field) <= next_day
                            )
                        )
                    )
                )
                
            elif operator == "before":
                return and_(
                    base_condition,
                    Node.id.in_(
                        select(Task.id).where(
                            getattr(Task, date_field) < date_value
                        )
                    )
                )
                
            elif operator == "after":
                return and_(
                    base_condition,
                    Node.id.in_(
                        select(Task.id).where(
                            getattr(Task, date_field) > date_value
                        )
                    )
                )
                
            elif operator == "between" and len(values) >= 2 and values[1]:
                end_date = datetime.fromisoformat(values[1]).replace(tzinfo=None)
                return and_(
                    base_condition,
                    Node.id.in_(
                        select(Task.id).where(
                            and_(
                                getattr(Task, date_field) >= date_value,
                                getattr(Task, date_field) <= end_date
                            )
                        )
                    )
                )
                
        except (ValueError, TypeError):
            pass
            
        return None
    
    def validate_rules(self, rules: Dict[str, Any]) -> List[str]:
        """Validate smart folder rules and return list of errors"""
        errors = []
        
        if not isinstance(rules, dict):
            errors.append("Rules must be a dictionary")
            return errors
        
        conditions = rules.get("conditions", [])
        if not isinstance(conditions, list):
            errors.append("Conditions must be a list")
            return errors
        
        logic = rules.get("logic", "AND")
        if logic not in ("AND", "OR"):
            errors.append("Logic must be 'AND' or 'OR'")
        
        for i, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                errors.append(f"Condition {i+1} must be a dictionary")
                continue
            
            condition_type = condition.get("type")
            if not condition_type:
                errors.append(f"Condition {i+1} missing 'type' field")
                continue
            
            valid_types = [
                "tag_contains", "node_type", "parent_node", 
                "task_status", "task_priority", "title_contains", "has_children",
                "due_date", "earliest_start", "saved_filter"
            ]
            if condition_type not in valid_types:
                errors.append(f"Condition {i+1} has invalid type: {condition_type}")
            
            operator = condition.get("operator")
            if not operator:
                errors.append(f"Condition {i+1} missing 'operator' field")
                continue
            
            values = condition.get("values", [])
            if not isinstance(values, list) or not values:
                errors.append(f"Condition {i+1} must have non-empty 'values' list")
        
        return errors