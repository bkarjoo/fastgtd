#!/usr/bin/env python3
"""
Test script to verify the is_today operator works through the API
"""
import asyncio
import sys
import httpx
from datetime import datetime, timezone

# Test the API directly to ensure is_today operator works end-to-end
async def test_is_today_through_api():
    """Test creating a rule with is_today operator through the Rules API"""
    print("🌐 Testing is_today operator through API...")
    
    # Create a test token (mock for testing)
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTU5ODgwMDcsInN1YiI6IjRjZTU3OWYzLTZjMzgtNDc4MC1hYzc1LTVhMTY4MjZkNGU2MiIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20ifQ.DgiTVumuFm1QUQInUjNIPRgslHwOeEm4s1UsuWkmbFo"
    
    headers = {
        "Authorization": f"Bearer {test_token}",
        "Content-Type": "application/json"
    }
    
    # Rule with is_today operator for due_date
    rule_data = {
        "name": "Tasks Due Today",
        "description": "Show all tasks that are due today",
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
    
    async with httpx.AsyncClient() as client:
        try:
            # Test creating a rule with is_today operator
            response = await client.post(
                "http://localhost:8003/rules/",
                headers=headers,
                json=rule_data
            )
            
            if response.status_code == 201:
                print("✅ Successfully created rule with is_today operator")
                created_rule = response.json()
                print(f"   Rule ID: {created_rule['id']}")
                print(f"   Rule Name: {created_rule['name']}")
                
                # Try to get the rule back
                get_response = await client.get(
                    f"http://localhost:8003/rules/{created_rule['id']}",
                    headers=headers
                )
                
                if get_response.status_code == 200:
                    print("✅ Successfully retrieved rule with is_today operator")
                    retrieved_rule = get_response.json()
                    
                    # Verify the rule data contains our is_today condition
                    conditions = retrieved_rule['rule_data']['conditions']
                    if any(c.get('operator') == 'is_today' for c in conditions):
                        print("✅ Rule correctly stored is_today operator")
                        return True
                    else:
                        print("❌ Rule did not store is_today operator correctly")
                        return False
                else:
                    print(f"❌ Failed to retrieve created rule: {get_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to create rule: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ API test failed with error: {e}")
            return False


async def main():
    """Run the API test"""
    success = await test_is_today_through_api()
    if success:
        print("\n🎉 API test passed! The is_today operator is working through the API.")
    else:
        print("\n❌ API test failed!")
    

if __name__ == "__main__":
    asyncio.run(main())