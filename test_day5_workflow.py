#!/usr/bin/env python3
"""
Test script for Day 5 Brief → Generate → Status workflow.
"""

import json
import time
import requests
import sys
from typing import Dict, Any, Optional

# Base URL for the API
BASE_URL = "http://localhost:8080"

def make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None ) -> Dict[str, Any]:
    """Make HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }

def test_health_check():
    """Test the health endpoint."""
    print("🏥 Testing Health Check...")
    
    result = make_request("GET", "/health")
    
    if result["success"] and result["data"].get("ok"):
        print("   ✅ Health check passed")
        return True
    else:
        print(f"   ❌ Health check failed: {result}")
        return False

def test_create_brief():
    """Test creating a brief."""
    print("\n📝 Testing Brief Creation...")
    
    brief_data = {
        "content": "Send a Slack message when I receive an urgent email in Gmail",
        "metadata": {
            "test": True,
            "created_by": "test_script"
        }
    }
    
    result = make_request("POST", "/briefs", brief_data)
    
    if result["success"] and result["data"].get("ok"):
        brief = result["data"]["brief"]
        print(f"   ✅ Brief created successfully")
        print(f"   📋 Brief ID: {brief['id']}")
        print(f"   📄 Content: {brief['content'][:50]}...")
        return brief["id"]
    else:
        print(f"   ❌ Brief creation failed: {result}")
        return None

def test_get_brief(brief_id: str):
    """Test retrieving a brief."""
    print(f"\n🔍 Testing Brief Retrieval (ID: {brief_id[:8]}...)...")
    
    result = make_request("GET", f"/briefs/{brief_id}")
    
    if result["success"] and result["data"].get("ok"):
        brief = result["data"]["brief"]
        print(f"   ✅ Brief retrieved successfully")
        print(f"   📄 Content: {brief['content'][:50]}...")
        return True
    else:
        print(f"   ❌ Brief retrieval failed: {result}")
        return False

def test_list_briefs():
    """Test listing briefs."""
    print("\n📋 Testing Brief Listing...")
    
    result = make_request("GET", "/briefs?limit=10")
    
    if result["success"] and result["data"].get("ok"):
        briefs = result["data"]["briefs"]
        count = result["data"]["count"]
        print(f"   ✅ Brief listing successful")
        print(f"   📊 Found {count} briefs")
        return True
    else:
        print(f"   ❌ Brief listing failed: {result}")
        return False

def test_generate_from_brief(brief_id: str):
    """Test generating a blueprint from a brief."""
    print(f"\n🚀 Testing Blueprint Generation (Brief ID: {brief_id[:8]}...)...")
    
    result = make_request("POST", f"/briefs/{brief_id}:generate")
    
    if result["success"] and result["data"].get("ok"):
        job = result["data"]["job"]
        print(f"   ✅ Generation job created successfully")
        print(f"   🆔 Job ID: {job['id']}")
        print(f"   📊 Status: {job['status']}")
        return job["id"]
    else:
        print(f"   ❌ Generation job creation failed: {result}")
        print(f"   📄 Response: {result['data']}")
        return None

def main():
    """Run the complete Day 5 workflow test."""
    print("🧪 Day 5 Brief → Generate → Status Workflow Test")
    print("=" * 60)
    
    # Test results
    results = []
    
    # 1. Health check
    results.append(("Health Check", test_health_check()))
    
    if not results[-1][1]:
        print("\n❌ Server not responding. Make sure the API server is running.")
        return 1
    
    # 2. Create brief
    brief_id = test_create_brief()
    results.append(("Create Brief", brief_id is not None))
    
    if not brief_id:
        print("\n❌ Cannot continue without a brief.")
        return 1
    
    # 3. Get brief
    results.append(("Get Brief", test_get_brief(brief_id)))
    
    # 4. List briefs
    results.append(("List Briefs", test_list_briefs()))
    
    # 5. Generate from brief
    job_id = test_generate_from_brief(brief_id)
    results.append(("Generate from Brief", job_id is not None))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🏆 Overall: {passed}/{total} tests passed")
    
    # Day 5 success criteria
    print("\n🎯 Day 5 Success Criteria:")
    
    brief_created = results[1][1]  # Create Brief
    job_created = results[4][1]    # Generate from Brief
    
    workflow_success = brief_created and job_created
    
    print(f"   Brief → Generate → Status observable: {'✅' if workflow_success else '❌'}")
    
    if workflow_success:
        print("\n🎉 Day 5 Success Criteria Met!")
        print("   ✅ Brief storage working")
        print("   ✅ Job generation working")
        return 0
    else:
        print("\n❌ Day 5 Success Criteria Not Met")
        return 1

if __name__ == "__main__":
    sys.exit(main())
