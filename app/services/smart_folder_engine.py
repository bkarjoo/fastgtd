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
        # Check if using new rule_id approach
        if smart_folder.rule_id:
            # Fetch the rule
            from app.models.rule import Rule
            rule_query = select(Rule).where(
                Rule.id == smart_folder.rule_id,
                or_(
                    Rule.owner_id == owner_id,
                    Rule.is_public == True,
                    Rule.is_system == True
                )
            )
            result = await self.session.execute(rule_query)
            rule = result.scalar_one_or_none()
            
            if not rule or not rule.rule_data:
                return []
            
            rules = rule.rule_data
        else:
            # Fall back to legacy inline rules
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
        
        if not condition_type or not operator:
            return None
        
        # Some operators don't require values (e.g., is_today, is_null, is_not_null)
        no_values_operators = ["is_today", "is_null", "is_not_null", "is_overdue", "this_week", "next_week", "this_month", "yesterday", "tomorrow"]
        if operator not in no_values_operators and not values:
            return None
        
        if condition_type == "node_type":
            return self._build_node_type_filter(operator, values)
        
        elif condition_type == "tag_contains":
            return await self._build_tag_filter(operator, values, owner_id)
        
        elif condition_type == "parent_node":
            return self._build_parent_filter(operator, values)
        
        elif condition_type == "parent_ancestor":
            return await self._build_ancestor_filter(operator, values)
        
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
    
    async def _build_ancestor_filter(self, operator: str, values: List[str]):
        """Build filter for ancestor node conditions (hierarchical parent search)"""
        try:
            if operator == "equals":
                ancestor_id = UUID(values[0])
                # Use recursive CTE to find all descendants of the ancestor
                return await self._build_descendants_subquery(ancestor_id)
            elif operator == "in":
                ancestor_uuids = [UUID(v) for v in values]
                # Combine multiple ancestor searches with OR
                conditions = []
                for ancestor_id in ancestor_uuids:
                    condition = await self._build_descendants_subquery(ancestor_id)
                    if condition is not None:
                        conditions.append(condition)
                return or_(*conditions) if conditions else None
        except (ValueError, TypeError):
            pass
        return None
    
    async def _build_descendants_subquery(self, ancestor_id: UUID):
        """Build a subquery to find all descendants of an ancestor node using recursive CTE"""
        from sqlalchemy import text
        
        # PostgreSQL recursive CTE to find all descendants
        descendants_cte = text("""
            WITH RECURSIVE node_hierarchy AS (
                -- Base case: direct children of the ancestor
                SELECT id, parent_id, title
                FROM nodes 
                WHERE parent_id = :ancestor_id
                
                UNION ALL
                
                -- Recursive case: children of already found nodes
                SELECT n.id, n.parent_id, n.title
                FROM nodes n
                INNER JOIN node_hierarchy nh ON n.parent_id = nh.id
            )
            SELECT id FROM node_hierarchy
        """)
        
        # Execute the CTE to get descendant IDs
        result = await self.session.execute(descendants_cte, {"ancestor_id": ancestor_id})
        descendant_ids = [row[0] for row in result.fetchall()]
        
        if descendant_ids:
            return Node.id.in_(descendant_ids)
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
            elif operator == "not_in":
                statuses = [TaskStatus(v) for v in values]
                return and_(
                    Node.node_type == "task",
                    Node.id.in_(
                        select(Task.id).where(~Task.status.in_(statuses))
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
            # No rule ID provided - filter out everything
            return False
            
        rule_id = values[0]
        
        # Import here to avoid circular imports
        from app.models.rule import Rule
        
        try:
            # Validate the rule_id is a valid UUID
            from uuid import UUID as validate_uuid
            validate_uuid(rule_id)
        except (ValueError, AttributeError):
            # Invalid UUID - filter out everything
            return False
        
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
            # Rule not found or has no data - filter out everything
            # This prevents showing all nodes when a rule is missing
            return False
        
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
        from datetime import datetime, timezone, timedelta
        
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
        
        elif operator == "is_today":
            # Handle "is_today" operator - no values needed
            today = datetime.now(timezone.utc).date()
            start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field) >= start_of_day,
                            getattr(Task, date_field) <= end_of_day
                        )
                    )
                )
            )
        
        # Phase 1: Overdue Detection (no values needed)
        elif operator == "is_overdue":
            # Due date is in the past (only applies to due_at field)
            if date_field != "due_at":
                return None
            today_start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time()).replace(tzinfo=timezone.utc)
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            Task.due_at.is_not(None),
                            Task.due_at < today_start
                        )
                    )
                )
            )
        
        # Phase 3: Calendar Periods (no values needed)
        elif operator == "this_week":
            # Current calendar week (Monday to Sunday)
            today = datetime.now(timezone.utc).date()
            # Calculate start of week (Monday)
            days_since_monday = today.weekday()  # Monday = 0, Sunday = 6
            week_start = today - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)
            
            start_of_week = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_week = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field).is_not(None),
                            getattr(Task, date_field) >= start_of_week,
                            getattr(Task, date_field) <= end_of_week
                        )
                    )
                )
            )
            
        elif operator == "next_week":
            # Next calendar week (Monday to Sunday)
            today = datetime.now(timezone.utc).date()
            days_since_monday = today.weekday()
            this_week_start = today - timedelta(days=days_since_monday)
            next_week_start = this_week_start + timedelta(days=7)
            next_week_end = next_week_start + timedelta(days=6)
            
            start_of_next_week = datetime.combine(next_week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_next_week = datetime.combine(next_week_end, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field).is_not(None),
                            getattr(Task, date_field) >= start_of_next_week,
                            getattr(Task, date_field) <= end_of_next_week
                        )
                    )
                )
            )
            
        elif operator == "this_month":
            # Current calendar month
            today = datetime.now(timezone.utc).date()
            month_start = today.replace(day=1)
            # Get last day of month
            if today.month == 12:
                next_month_start = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month_start = today.replace(month=today.month + 1, day=1)
            month_end = next_month_start - timedelta(days=1)
            
            start_of_month = datetime.combine(month_start, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_month = datetime.combine(month_end, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field).is_not(None),
                            getattr(Task, date_field) >= start_of_month,
                            getattr(Task, date_field) <= end_of_month
                        )
                    )
                )
            )
            
        elif operator == "yesterday":
            # Date was yesterday
            yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
            start_of_day = datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(yesterday, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field) >= start_of_day,
                            getattr(Task, date_field) <= end_of_day
                        )
                    )
                )
            )
            
        elif operator == "tomorrow":
            # Date is tomorrow
            tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
            start_of_day = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(tomorrow, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            return and_(
                base_condition,
                Node.id.in_(
                    select(Task.id).where(
                        and_(
                            getattr(Task, date_field) >= start_of_day,
                            getattr(Task, date_field) <= end_of_day
                        )
                    )
                )
            )
        
        # Operators that require values
        if not values or not values[0]:
            return None
            
        # Phase 1: Overdue Detection (with values)
        if operator in ["overdue_by_days", "overdue_by_more_than", "overdue_by_less_than"]:
            if date_field != "due_at":  # Only applies to due dates
                return None
            try:
                days = int(values[0])
                today = datetime.now(timezone.utc).date()
                
                if operator == "overdue_by_days":
                    # Overdue by exactly N days
                    target_date = today - timedelta(days=days)
                    start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    Task.due_at >= start_of_day,
                                    Task.due_at <= end_of_day
                                )
                            )
                        )
                    )
                elif operator == "overdue_by_more_than":
                    # Overdue by more than N days
                    cutoff_date = today - timedelta(days=days)
                    cutoff_end = datetime.combine(cutoff_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    Task.due_at.is_not(None),
                                    Task.due_at < cutoff_end
                                )
                            )
                        )
                    )
                elif operator == "overdue_by_less_than":
                    # Overdue by less than N days
                    cutoff_date = today - timedelta(days=days)
                    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                    cutoff_start = datetime.combine(cutoff_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    Task.due_at.is_not(None),
                                    Task.due_at < today_start,
                                    Task.due_at >= cutoff_start
                                )
                            )
                        )
                    )
            except (ValueError, TypeError):
                return None
        
        # Phase 1: Upcoming/Due Soon (with values)
        elif operator in ["due_in_days", "due_within_days", "due_in_more_than_days"]:
            try:
                days = int(values[0])
                today = datetime.now(timezone.utc).date()
                
                if operator == "due_in_days":
                    # Due in exactly N days
                    target_date = today + timedelta(days=days)
                    start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field) >= start_of_day,
                                    getattr(Task, date_field) <= end_of_day
                                )
                            )
                        )
                    )
                elif operator == "due_within_days":
                    # Due within next N days (includes today)
                    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                    end_date = today + timedelta(days=days)
                    end_of_period = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field).is_not(None),
                                    getattr(Task, date_field) >= today_start,
                                    getattr(Task, date_field) <= end_of_period
                                )
                            )
                        )
                    )
                elif operator == "due_in_more_than_days":
                    # Due more than N days from now
                    cutoff_date = today + timedelta(days=days)
                    cutoff_end = datetime.combine(cutoff_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field).is_not(None),
                                    getattr(Task, date_field) > cutoff_end
                                )
                            )
                        )
                    )
            except (ValueError, TypeError):
                return None
        
        # Phase 2: Relative Date Ranges (with values)
        elif operator in ["within_last_days", "more_than_days_ago", "exactly_days_ago", 
                         "within_next_days", "starts_within_days", "starts_in_more_than_days"]:
            try:
                days = int(values[0])
                today = datetime.now(timezone.utc).date()
                
                if operator == "within_last_days":
                    # Date within last N days (includes today)
                    start_date = today - timedelta(days=days)
                    start_of_period = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field).is_not(None),
                                    getattr(Task, date_field) >= start_of_period,
                                    getattr(Task, date_field) <= today_end
                                )
                            )
                        )
                    )
                elif operator == "more_than_days_ago":
                    # Date more than N days ago
                    cutoff_date = today - timedelta(days=days)
                    cutoff_start = datetime.combine(cutoff_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field).is_not(None),
                                    getattr(Task, date_field) < cutoff_start
                                )
                            )
                        )
                    )
                elif operator == "exactly_days_ago":
                    # Date exactly N days ago
                    target_date = today - timedelta(days=days)
                    start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
                    end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field) >= start_of_day,
                                    getattr(Task, date_field) <= end_of_day
                                )
                            )
                        )
                    )
                elif operator == "within_next_days":
                    # Date within next N days (includes today)
                    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                    end_date = today + timedelta(days=days)
                    end_of_period = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                    return and_(
                        base_condition,
                        Node.id.in_(
                            select(Task.id).where(
                                and_(
                                    getattr(Task, date_field).is_not(None),
                                    getattr(Task, date_field) >= today_start,
                                    getattr(Task, date_field) <= end_of_period
                                )
                            )
                        )
                    )
                elif operator in ["starts_within_days", "starts_in_more_than_days"]:
                    # These are aliases for due date logic but more semantic for start dates
                    if operator == "starts_within_days":
                        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
                        end_date = today + timedelta(days=days)
                        end_of_period = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                        return and_(
                            base_condition,
                            Node.id.in_(
                                select(Task.id).where(
                                    and_(
                                        getattr(Task, date_field).is_not(None),
                                        getattr(Task, date_field) >= today_start,
                                        getattr(Task, date_field) <= end_of_period
                                    )
                                )
                            )
                        )
                    else:  # starts_in_more_than_days
                        cutoff_date = today + timedelta(days=days)
                        cutoff_end = datetime.combine(cutoff_date, datetime.max.time()).replace(tzinfo=timezone.utc)
                        return and_(
                            base_condition,
                            Node.id.in_(
                                select(Task.id).where(
                                    and_(
                                        getattr(Task, date_field).is_not(None),
                                        getattr(Task, date_field) > cutoff_end
                                    )
                                )
                            )
                        )
            except (ValueError, TypeError):
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
                "tag_contains", "node_type", "parent_node", "parent_ancestor",
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
            if not isinstance(values, list):
                errors.append(f"Condition {i+1} 'values' must be a list")
                continue
                
            # Some operators don't require values (e.g., is_today, is_null, is_not_null)
            no_values_operators = ["is_today", "is_null", "is_not_null", "is_overdue", "this_week", "next_week", "this_month", "yesterday", "tomorrow"]
            if operator not in no_values_operators and not values:
                errors.append(f"Condition {i+1} must have non-empty 'values' list")
        
        return errors