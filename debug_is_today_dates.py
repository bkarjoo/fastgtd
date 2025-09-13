#!/usr/bin/env python3
"""
Debug script to understand the date handling in is_today operator
"""
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from uuid import UUID

sys.path.append('.')

from app.services.smart_folder_engine import SmartFolderRulesEngine
from app.db.session import get_sessionmaker
from app.models.node import Node, Task
from sqlalchemy import select, and_

async def debug_is_today_dates():
    """Debug the date handling and filtering logic"""
    print("🔍 Debugging is_today operator date handling...")
    
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        engine = SmartFolderRulesEngine(session)
        
        # Check what today looks like
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        print(f"\n📅 Date calculations:")
        print(f"   Today (date): {today}")
        print(f"   Start of day: {start_of_day}")
        print(f"   End of day: {end_of_day}")
        
        # Query all tasks to see their due dates
        print(f"\n📋 All tasks in database:")
        result = await session.execute(
            select(Node, Task).join(Task, Node.id == Task.id).where(Node.node_type == "task")
        )
        tasks = result.all()
        
        for node, task in tasks:
            print(f"   Task: {node.title}")
            print(f"     ID: {node.id}")
            print(f"     Due at: {task.due_at}")
            print(f"     Earliest start: {task.earliest_start_at}")
            if task.due_at:
                is_today_due = start_of_day <= task.due_at <= end_of_day
                print(f"     Is due today: {is_today_due}")
            if task.earliest_start_at:
                is_today_start = start_of_day <= task.earliest_start_at <= end_of_day
                print(f"     Starts today: {is_today_start}")
            print()
        
        # Test the date filter directly
        print(f"\n🔧 Testing _build_date_filter directly:")
        owner_id = UUID('d62ce8f5-2e33-44e4-860c-15f38734caee')
        
        # Test due_date is_today filter
        filter_condition = engine._build_date_filter("is_today", [], "due_at")
        print(f"   Due date filter created: {filter_condition is not None}")
        
        if filter_condition is not None:
            # Build query to test the filter
            query = select(Node).where(
                and_(
                    Node.owner_id == owner_id,
                    filter_condition
                )
            )
            
            result = await session.execute(query)
            matching_nodes = result.scalars().all()
            print(f"   Nodes matching due_date is_today: {len(matching_nodes)}")
            for node in matching_nodes:
                print(f"     - {node.title} ({node.id})")
        
        # Test earliest_start is_today filter
        filter_condition2 = engine._build_date_filter("is_today", [], "earliest_start_at")
        print(f"   Earliest start filter created: {filter_condition2 is not None}")
        
        if filter_condition2 is not None:
            # Build query to test the filter
            query2 = select(Node).where(
                and_(
                    Node.owner_id == owner_id,
                    filter_condition2
                )
            )
            
            result2 = await session.execute(query2)
            matching_nodes2 = result2.scalars().all()
            print(f"   Nodes matching earliest_start is_today: {len(matching_nodes2)}")
            for node in matching_nodes2:
                print(f"     - {node.title} ({node.id})")

async def main():
    """Run the debug analysis"""
    await debug_is_today_dates()

if __name__ == "__main__":
    asyncio.run(main())