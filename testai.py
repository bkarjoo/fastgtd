#!/usr/bin/env python3
"""
FastGTD AI Testing Script

This script provides a simple way to test the FastGTD AI interface and MCP tools
without having to use the web interface. It maintains conversation history and 
handles authentication automatically.

Why this exists:
- MCP tool development was frustrating because testing required the web interface
- No easy way to test AI responses and tool calls directly
- Need persistent conversation history for context
- Want to quickly iterate on prompts and see responses

Usage:
    python testai.py "search for cabinet tasks"
    python testai.py --clear "start fresh conversation"
    python testai.py --help

Features:
- Auto-authenticates as test user (bkarjoo@gmail.com)
- Maintains conversation history in testai_history.json
- Shows AI responses including MCP tool calls
- Can clear history to start fresh conversations
"""

import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import httpx
import asyncio

# Add the project root to Python path so we can import FastGTD modules
sys.path.append('.')

HISTORY_FILE = "testai_history.json"
TEST_USER_EMAIL = "bkarjoo@gmail.com"
TEST_USER_PASSWORD = "333928"
BASE_URL = "http://localhost:8003"

def load_conversation_history():
    """Load existing conversation history from file"""
    try:
        if Path(HISTORY_FILE).exists():
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load history file: {e}")
    
    return []

def save_conversation_history(history):
    """Save conversation history to file"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save history file: {e}")

def clear_conversation_history():
    """Clear the conversation history file"""
    try:
        if Path(HISTORY_FILE).exists():
            os.remove(HISTORY_FILE)
            print(f"✅ Cleared conversation history ({HISTORY_FILE})")
        else:
            print("ℹ️  No conversation history to clear")
    except Exception as e:
        print(f"❌ Error clearing history: {e}")

async def get_auth_token():
    """
    Authenticate with FastGTD and get an access token for the test user.
    Hardcoded credentials: bkarjoo@gmail.com / 333298
    """
    print(f"🔐 Authenticating as {TEST_USER_EMAIL}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    print("✅ Authentication successful")
                    return token
                else:
                    print("❌ No access token in response")
                    return None
            else:
                print(f"❌ Authentication failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

async def call_ai_endpoint(prompt, auth_token, conversation_history):
    """
    Call the FastGTD AI endpoint with the prompt and conversation history.
    Returns the AI response or None if failed.
    """
    print(f"🤖 Sending prompt to AI: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
    
    try:
        # Prepare the conversation context
        messages = []
        
        # Add conversation history
        for entry in conversation_history:
            messages.append({"role": "user", "content": entry["prompt"]})
            messages.append({"role": "assistant", "content": entry["response"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            # Set context first (required by FastGTD AI router)
            await client.post(
                f"{BASE_URL}/ai/set-context",
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=10.0
            )
            
            # Make the AI chat request with conversation history
            response = await client.post(
                f"{BASE_URL}/ai/chat",
                json={
                    "message": prompt,
                    "history": messages[:-1] if messages else []  # Exclude current message as it's sent separately
                },
                headers={"Authorization": f"Bearer {auth_token}"},
                timeout=30.0  # AI calls can take longer
            )
            
            if response.status_code == 200:
                ai_data = response.json()
                ai_response = ai_data.get("response", "No response in data")
                print("✅ AI response received")
                print(f"🔍 Actions taken: {ai_data.get('actions_taken', False)}")
                return ai_response
            else:
                print(f"❌ AI request failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ AI request error: {e}")
        return None

def print_response(response):
    """Pretty print the AI response"""
    print("\n" + "="*60)
    print("🤖 AI RESPONSE:")
    print("="*60)
    print(response)
    print("="*60 + "\n")

async def main():
    """Main function that handles command line args and orchestrates the test"""
    
    parser = argparse.ArgumentParser(
        description="Test FastGTD AI interface and MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python testai.py "search for cabinet tasks"
  python testai.py "create a task called 'test task'"
  python testai.py --clear "start a new conversation"
  
This script maintains conversation history in testai_history.json
Use --clear to start fresh conversations.
        """
    )
    
    parser.add_argument(
        "prompt", 
        help="The prompt/message to send to the AI"
    )
    
    parser.add_argument(
        "--clear", 
        action="store_true",
        help="Clear conversation history before sending the prompt"
    )
    
    args = parser.parse_args()
    
    # Clear history if requested
    if args.clear:
        clear_conversation_history()
    
    # Load existing conversation history
    conversation_history = load_conversation_history()
    print(f"📚 Loaded {len(conversation_history)} previous conversation(s)")
    
    # Get authentication token
    auth_token = await get_auth_token()
    if not auth_token:
        print("❌ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Call the AI endpoint
    ai_response = await call_ai_endpoint(args.prompt, auth_token, conversation_history)
    if not ai_response:
        print("❌ Failed to get AI response")
        sys.exit(1)
    
    # Print the response
    print_response(ai_response)
    
    # Add to conversation history
    conversation_entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": args.prompt,
        "response": ai_response
    }
    
    conversation_history.append(conversation_entry)
    
    # Save updated history
    save_conversation_history(conversation_history)
    print(f"💾 Conversation saved to {HISTORY_FILE}")

if __name__ == "__main__":
    asyncio.run(main())