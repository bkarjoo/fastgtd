#!/usr/bin/env python3
"""
Complete end-to-end test for is_today operator functionality
Tests creating rules, smart folders, and validating the complete pipeline
"""
import asyncio
import sys
import httpx
from datetime import datetime, timezone, timedelta
from uuid import uuid4

async def test_complete_is_today_functionality():
    """Complete test of is_today operator from API to rule evaluation"""
    print("🔄 Testing complete is_today operator functionality...")
    
    # Generate fresh auth token
    from app.core.security import create_access_token
    user_id = 'd62ce8f5-2e33-44e4-860c-15f38734caee'
    extra_claims = {'email': 'bkarjoo@gmail.com'}
    token = create_access_token(subject=user_id, extra_claims=extra_claims)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Create rule with is_today for due_date
            print("\n📋 Test 1: Creating rule with due_date is_today")
            rule_data = {
                "name": "Tasks Due Today - Complete Test",
                "description": "Complete test rule with is_today operator for due dates",
                "rule_data": {
                    "conditions": [
                        {
                            "type": "due_date",
                            "operator": "is_today",
                            "values": []
                        }
                    ],
                    "logic": "AND"
                },
                "is_public": False
            }
            
            response = await client.post(
                "http://localhost:8003/rules/",
                headers=headers,
                json=rule_data
            )
            
            if response.status_code != 201:
                print(f"❌ Failed to create due_date rule: {response.status_code} - {response.text}")
                return False
            
            due_rule = response.json()
            print(f"✅ Created due_date rule: {due_rule['id']}")
            
            # Test 2: Create rule with is_today for earliest_start
            print("\n📋 Test 2: Creating rule with earliest_start is_today")
            rule_data2 = {
                "name": "Tasks Starting Today - Complete Test",
                "description": "Complete test rule with is_today operator for earliest_start",
                "rule_data": {
                    "conditions": [
                        {
                            "type": "earliest_start",
                            "operator": "is_today",
                            "values": []
                        }
                    ],
                    "logic": "AND"
                },
                "is_public": False
            }
            
            response = await client.post(
                "http://localhost:8003/rules/",
                headers=headers,
                json=rule_data2
            )
            
            if response.status_code != 201:
                print(f"❌ Failed to create earliest_start rule: {response.status_code} - {response.text}")
                return False
            
            start_rule = response.json()
            print(f"✅ Created earliest_start rule: {start_rule['id']}")
            
            # Test 3: Create test tasks with today's dates
            print("\n📝 Test 3: Creating test tasks with today's dates")
            today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            yesterday = today - timedelta(days=1)
            
            # Task due today
            task_due_today = {
                "node_type": "task",
                "title": "Task Due Today Test",
                "task_data": {
                    "description": "Test task due today",
                    "priority": "medium",
                    "status": "todo",
                    "due_at": today.isoformat(),
                    "archived": False
                }
            }
            
            response = await client.post(
                "http://localhost:8003/nodes/",
                headers=headers,
                json=task_due_today
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create task due today: {response.status_code} - {response.text}")
                return False
            
            task1 = response.json()
            print(f"✅ Created task due today: {task1['id']}")
            
            # Task starting today
            task_start_today = {
                "node_type": "task",
                "title": "Task Starting Today Test",
                "task_data": {
                    "description": "Test task starting today",
                    "priority": "high",
                    "status": "todo",
                    "earliest_start_at": today.isoformat(),
                    "archived": False
                }
            }
            
            response = await client.post(
                "http://localhost:8003/nodes/",
                headers=headers,
                json=task_start_today
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create task starting today: {response.status_code} - {response.text}")
                return False
            
            task2 = response.json()
            print(f"✅ Created task starting today: {task2['id']}")
            
            # Control task (not today)
            task_tomorrow = {
                "node_type": "task",
                "title": "Task Due Tomorrow Test",
                "task_data": {
                    "description": "Test task due tomorrow (should not match)",
                    "priority": "low",
                    "status": "todo",
                    "due_at": tomorrow.isoformat(),
                    "archived": False
                }
            }
            
            response = await client.post(
                "http://localhost:8003/nodes/",
                headers=headers,
                json=task_tomorrow
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create control task: {response.status_code} - {response.text}")
                return False
            
            task3 = response.json()
            print(f"✅ Created control task (tomorrow): {task3['id']}")
            
            # Test 4: Create smart folders using the rules
            print("\n🤖 Test 4: Creating smart folders with is_today rules")
            
            # Smart folder for tasks due today
            smart_folder1 = {
                "node_type": "smart_folder",
                "title": "Due Today Smart Folder Test",
                "smart_folder_data": {
                    "rule_id": due_rule['id'],
                    "auto_refresh": True,
                    "description": "Smart folder showing tasks due today"
                }
            }
            
            response = await client.post(
                "http://localhost:8003/nodes/",
                headers=headers,
                json=smart_folder1
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create due today smart folder: {response.status_code} - {response.text}")
                return False
            
            sf1 = response.json()
            print(f"✅ Created due today smart folder: {sf1['id']}")
            
            # Smart folder for tasks starting today
            smart_folder2 = {
                "node_type": "smart_folder",
                "title": "Starting Today Smart Folder Test",
                "smart_folder_data": {
                    "rule_id": start_rule['id'],
                    "auto_refresh": True,
                    "description": "Smart folder showing tasks starting today"
                }
            }
            
            response = await client.post(
                "http://localhost:8003/nodes/",
                headers=headers,
                json=smart_folder2
            )
            
            if response.status_code not in [200, 201]:
                print(f"❌ Failed to create starting today smart folder: {response.status_code} - {response.text}")
                return False
            
            sf2 = response.json()
            print(f"✅ Created starting today smart folder: {sf2['id']}")
            
            # Test 5: Verify smart folder contents
            print("\n🔍 Test 5: Verifying smart folder contents")
            
            # Get contents of due today smart folder
            response = await client.get(
                f"http://localhost:8003/nodes/{sf1['id']}/contents",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get due today smart folder contents: {response.status_code} - {response.text}")
                return False
            
            due_today_contents = response.json()
            print(f"📊 Due today smart folder contents: {len(due_today_contents)} items")
            
            # Check if our "due today" task is in the results
            due_today_task_found = any(item['id'] == task1['id'] for item in due_today_contents)
            tomorrow_task_in_due = any(item['id'] == task3['id'] for item in due_today_contents)
            
            if due_today_task_found:
                print("✅ Task due today correctly found in due today smart folder")
            else:
                print("❌ Task due today NOT found in due today smart folder")
                return False
            
            if not tomorrow_task_in_due:
                print("✅ Task due tomorrow correctly excluded from due today smart folder")
            else:
                print("❌ Task due tomorrow incorrectly included in due today smart folder")
                return False
            
            # Get contents of starting today smart folder
            response = await client.get(
                f"http://localhost:8003/nodes/{sf2['id']}/contents",
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to get starting today smart folder contents: {response.status_code} - {response.text}")
                return False
            
            start_today_contents = response.json()
            print(f"📊 Starting today smart folder contents: {len(start_today_contents)} items")
            
            # Check if our "starting today" task is in the results
            start_today_task_found = any(item['id'] == task2['id'] for item in start_today_contents)
            
            if start_today_task_found:
                print("✅ Task starting today correctly found in starting today smart folder")
            else:
                print("❌ Task starting today NOT found in starting today smart folder")
                return False
            
            print("\n🎉 All tests passed! The is_today operator is working correctly end-to-end!")
            print("\n📊 Summary:")
            print(f"   • Created 2 rules with is_today operator")
            print(f"   • Created 3 test tasks (2 today, 1 tomorrow)")
            print(f"   • Created 2 smart folders using the rules")
            print(f"   • Verified correct filtering behavior")
            print(f"   • Tasks due today: {len([item for item in due_today_contents if item['node_type'] == 'task'])}")
            print(f"   • Tasks starting today: {len([item for item in start_today_contents if item['node_type'] == 'task'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return False


async def main():
    """Run the complete functionality test"""
    print("🧪 Starting complete is_today operator functionality test...")
    
    # Add the project root to Python path
    sys.path.append('.')
    
    success = await test_complete_is_today_functionality()
    if success:
        print("\n✅ Complete functionality test PASSED!")
        print("🎯 The is_today operator is fully functional!")
    else:
        print("\n❌ Complete functionality test FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())