#!/usr/bin/env python3
"""
Test script for Day 7 Test Harness functionality.
Tests with GB-1 to verify at least 1 passing test.
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

def test_day7_harness():
    """Test the complete Day 7 test harness functionality."""
    print("🧪 Day 7 Test Harness Test")
    print("=" * 50)
    
    # Step 1: Create test payloads
    print("\n📝 Step 1: Creating test payloads...")
    
    # GB-1 style payload (Gmail urgent email)
    gb1_payload = {
        "name": "GB-1 Gmail Urgent Email",
        "description": "Test payload for urgent Gmail email automation",
        "data": {
            "email": {
                "subject": "URGENT: Server Down",
                "from": "alerts@company.com",
                "body": "The production server is experiencing issues.",
                "labels": ["URGENT", "INBOX"],
                "timestamp": time.time()
            }
        },
        "expected_output": {
            "action": "email_processed",
            "subject": "URGENT: Server Down"
        }
    }
    
    result = make_request("POST", "/test/payloads", gb1_payload)
    if not result["success"]:
        print(f"❌ Failed to create GB-1 payload: {result}")
        return False
    
    gb1_payload_id = result["data"]["payload"]["id"]
    print(f"✅ GB-1 payload created: {gb1_payload_id[:8]}...")
    
    # Step 2: Create additional test payload
    slack_payload = {
        "name": "Slack Message Test",
        "description": "Test payload for Slack message processing",
        "data": {
            "message": {
                "text": "Hello from test harness!",
                "channel": "#general",
                "user": "testbot",
                "timestamp": time.time()
            }
        }
    }
    
    result = make_request("POST", "/test/payloads", slack_payload)
    if not result["success"]:
        print(f"❌ Failed to create Slack payload: {result}")
        return False
    
    slack_payload_id = result["data"]["payload"]["id"]
    print(f"✅ Slack payload created: {slack_payload_id[:8]}...")
    
    # Step 3: List payloads
    print("\n📋 Step 3: Listing test payloads...")
    result = make_request("GET", "/test/payloads")
    if result["success"]:
        payloads = result["data"]["payloads"]
        print(f"✅ Found {len(payloads)} test payloads")
        for payload in payloads:
            print(f"   - {payload['name']}: {payload['id'][:8]}...")
    else:
        print(f"❌ Failed to list payloads: {result}")
        return False
    
    # Step 4: Run tests
    print("\n🚀 Step 4: Running tests...")
    
    # Run GB-1 test
    print("   Testing GB-1 payload...")
    result = make_request("POST", f"/test/payloads/{gb1_payload_id}:run")
    if not result["success"]:
        print(f"❌ Failed to run GB-1 test: {result}")
        return False
    
    gb1_result_id = result["data"]["test_result"]["id"]
    gb1_status = result["data"]["test_result"]["status"]
    print(f"✅ GB-1 test executed: {gb1_status}")
    
    # Run Slack test with mock webhook
    print("   Testing Slack payload with mock webhook...")
    webhook_data = {"webhook_url": "https://hooks.slack.com/test/mock/webhook"}
    result = make_request("POST", f"/test/payloads/{slack_payload_id}:run", webhook_data )
    if not result["success"]:
        print(f"❌ Failed to run Slack test: {result}")
        return False
    
    slack_result_id = result["data"]["test_result"]["id"]
    slack_status = result["data"]["test_result"]["status"]
    print(f"✅ Slack test executed: {slack_status}")
    
    # Step 5: Check test results
    print("\n📊 Step 5: Checking test results...")
    
    # Get GB-1 result details
    result = make_request("GET", f"/test/results/{gb1_result_id}")
    if result["success"]:
        gb1_result = result["data"]["result"]
        print(f"✅ GB-1 result: {gb1_result['status']} ({gb1_result['execution_time']:.3f}s)")
        if gb1_result.get("error_message"):
            print(f"   Error: {gb1_result['error_message']}")
    else:
        print(f"❌ Failed to get GB-1 result: {result}")
        return False
    
    # Get test summary
    result = make_request("GET", "/test/summary")
    if result["success"]:
        summary = result["data"]["summary"]
        print(f"✅ Test summary:")
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        
        # Check Day 7 success criteria
        has_passing_test = summary['passed'] > 0
        gb1_passed = gb1_status == "passed"
        
        return has_passing_test and gb1_passed
    else:
        print(f"❌ Failed to get test summary: {result}")
        return False

def test_validation_report_with_tests():
    """Test validation report generation with test results."""
    print("\n📄 Step 6: Testing validation report with test results...")
    
    try:
        from app.document_generator import document_generator
        from app.test_harness import test_harness
        
        # Mock blueprint (GB-1 style)
        mock_blueprint = {
            "version": "v1.0",
            "triggerId": "gmail-urgent-trigger",
            "modules": [
                {
                    "id": "gmail-urgent-trigger",
                    "type": "trigger",
                    "name": "Gmail Urgent Email Trigger",
                    "params": {"app": "Gmail", "filter": "subject:URGENT"}
                },
                {
                    "id": "slack-notification",
                    "type": "action",
                    "name": "Send Slack Notification", 
                    "params": {"app": "Slack", "channel": "#alerts"}
                }
            ],
            "connections": [{"from": "gmail-urgent-trigger", "to": "slack-notification"}]
        }
        
        # Mock lint result
        lint_result = {"ok": True, "violations": [], "count": 0}
        
        # Get test summary
        test_summary = test_harness.get_test_summary()
        
        # Generate validation report with tests
        report = document_generator.generate_validation_report_with_tests(
            mock_blueprint, lint_result, test_summary
        )
        
        print(f"✅ Validation report generated with test results")
        print(f"   Report length: {len(report)} characters")
        
        # Check if test results are included
        if "Test Results" in report and "Test Execution Summary" in report:
            print("✅ Test results properly integrated into validation report")
            return True
        else:
            print("❌ Test results not found in validation report")
            return False
            
    except Exception as e:
        print(f"❌ Validation report test failed: {e}")
        return False

def main():
    """Run the complete Day 7 test."""
    print("🧪 Day 7 Test Harness Complete Test")
    print("=" * 60)
    
    # Test API endpoints
    api_success = test_day7_harness()
    
    # Test validation report integration
    report_success = test_validation_report_with_tests()
    
    print("\n" + "=" * 60)
    print("📊 Day 7 Test Results:")
    
    if api_success:
        print("✅ Test harness API: WORKING")
        print("✅ Payload management: WORKING")
        print("✅ Test execution: WORKING")
        print("✅ GB-1 test: PASSING")
    else:
        print("❌ Test harness functionality: FAILED")
    
    if report_success:
        print("✅ Validation report integration: WORKING")
    else:
        print("❌ Validation report integration: FAILED")
    
    print("\n🎯 Day 7 Success Criteria:")
    gb1_success = api_success  # GB-1 shows at least 1 passing test
    
    if gb1_success:
        print("✅ GB-1 shows at least 1 passing test - SUCCESS!")
        print("\n🎉 Day 7 Complete!")
        return 0
    else:
        print("❌ GB-1 success criteria not met")
        return 1

if __name__ == "__main__":
    sys.exit(main())
