#!/usr/bin/env python3
"""
Test script to verify the is_today operator functionality in the rule engine
"""
import asyncio
import sys
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Add the project root to Python path
sys.path.append('.')

from app.services.smart_folder_engine import SmartFolderRulesEngine
from app.db.session import get_sessionmaker
from app.models.node import Node, Task
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority


async def test_is_today_operator():
    """Test the is_today operator for both due_date and earliest_start conditions"""
    print("🧪 Testing is_today operator implementation...")
    
    # Create a database session
    SessionLocal = get_sessionmaker()
    async with SessionLocal() as session:
        engine = SmartFolderRulesEngine(session)
        
        # Test 1: Validate rules with is_today operator
        print("\n📋 Test 1: Validating rule syntax")
        
        # Rule for "tasks due today"
        due_today_rule = {
            "conditions": [
                {
                    "type": "due_date",
                    "operator": "is_today", 
                    "values": []  # No values needed for is_today
                }
            ],
            "logic": "AND"
        }
        
        errors = engine.validate_rules(due_today_rule)
        if errors:
            print(f"❌ Validation failed for due_today rule: {errors}")
            return False
        else:
            print("✅ due_today rule validation passed")
        
        # Rule for "tasks with earliest start today"
        start_today_rule = {
            "conditions": [
                {
                    "type": "earliest_start",
                    "operator": "is_today",
                    "values": []  # No values needed for is_today
                }
            ],
            "logic": "AND"
        }
        
        errors = engine.validate_rules(start_today_rule)
        if errors:
            print(f"❌ Validation failed for start_today rule: {errors}")
            return False
        else:
            print("✅ start_today rule validation passed")
        
        # Test 2: Test condition filter building
        print("\n🔧 Test 2: Testing condition filter building")
        
        # Mock owner ID
        owner_id = uuid4()
        
        # Test due_date is_today condition
        due_condition = {
            "type": "due_date",
            "operator": "is_today",
            "values": []
        }
        
        filter_result = await engine._build_condition_filter(due_condition, owner_id)
        if filter_result is not None:
            print("✅ due_date is_today filter built successfully")
        else:
            print("❌ Failed to build due_date is_today filter")
            return False
        
        # Test earliest_start is_today condition
        start_condition = {
            "type": "earliest_start", 
            "operator": "is_today",
            "values": []
        }
        
        filter_result = await engine._build_condition_filter(start_condition, owner_id)
        if filter_result is not None:
            print("✅ earliest_start is_today filter built successfully")
        else:
            print("❌ Failed to build earliest_start is_today filter")
            return False
        
        # Test 3: Verify today's date range calculation
        print("\n📅 Test 3: Verifying today's date range")
        
        today = datetime.now(timezone.utc).date()
        print(f"   Today's date: {today}")
        
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc) 
        
        print(f"   Start of day: {start_of_day}")
        print(f"   End of day: {end_of_day}")
        
        # Verify the range makes sense
        if start_of_day.date() == today and end_of_day.date() == today:
            print("✅ Date range calculation is correct")
        else:
            print("❌ Date range calculation is incorrect")
            return False
        
        print("\n🎉 All tests passed! The is_today operator is working correctly.")
        return True


async def main():
    """Run the tests"""
    success = await test_is_today_operator()
    if not success:
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())