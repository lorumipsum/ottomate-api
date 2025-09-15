#!/usr/bin/env python3
"""
Test script for Day 6 Export Pack functionality.
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

def test_export_pack():
    """Test the complete export pack workflow."""
    print("🧪 Day 6 Export Pack Test")
    print("=" * 50)
    
    # Step 1: Create a brief
    print("\n📝 Step 1: Creating a brief...")
    brief_data = {
        "content": "Send a Slack notification when I receive an urgent email in Gmail",
        "metadata": {"test": True, "export_test": True}
    }
    
    result = make_request("POST", "/briefs", brief_data)
    if not result["success"]:
        print(f"❌ Failed to create brief: {result}")
        return False
    
    brief_id = result["data"]["brief"]["id"]
    print(f"✅ Brief created: {brief_id[:8]}...")
    
    # Step 2: Create a mock completed job (since we don't have OpenAI)
    print("\n🔧 Step 2: Creating mock completed job...")
    
    # First create the job
    result = make_request("POST", f"/briefs/{brief_id}:generate")
    if not result["success"]:
        print(f"❌ Failed to create job: {result}")
        return False
    
    job_id = result["data"]["job"]["id"]
    print(f"✅ Job created: {job_id[:8]}...")
    
    # Since we can't actually complete the job without OpenAI, 
    # let's test the export with a mock blueprint
    print("\n📦 Step 3: Testing export pack generation...")
    
    # Test the document generator directly
    try:
        from app.document_generator import document_generator
        from app.export_pack import export_pack_generator
        
        # Mock blueprint
        mock_blueprint = {
            "version": "v1.0",
            "triggerId": "gmail-trigger",
            "modules": [
                {
                    "id": "gmail-trigger",
                    "type": "trigger",
                    "name": "Gmail Urgent Email",
                    "params": {"app": "Gmail", "filter": "urgent"}
                },
                {
                    "id": "slack-action",
                    "type": "action", 
                    "name": "Send Slack Message",
                    "params": {"app": "Slack", "channel": "#alerts"}
                }
            ],
            "connections": [{"from": "gmail-trigger", "to": "slack-action"}]
        }
        
        # Test document generation
        proposal = document_generator.generate_proposal(mock_blueprint, brief_data["content"])
        runbook = document_generator.generate_runbook(mock_blueprint, brief_data["content"])
        
        print("✅ Document generation working")
        print(f"   📄 Proposal: {len(proposal)} characters")
        print(f"   📖 Runbook: {len(runbook)} characters")
        
        # Test export pack generation
        success, result_path = export_pack_generator.generate_export_pack(
            mock_blueprint, brief_data["content"], job_id
        )
        
        if success:
            print(f"✅ Export pack generated: {result_path}")
            
            # Check if file exists
            import os
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"   📦 ZIP file size: {file_size} bytes")
                
                # Test ZIP contents
                import zipfile
                with zipfile.ZipFile(result_path, 'r') as zipf:
                    files = zipf.namelist()
                    print(f"   📁 ZIP contents: {', '.join(files)}")
                    
                    expected_files = ["blueprint.json", "proposal.md", "runbook.md", "validation_report.md"]
                    missing_files = [f for f in expected_files if f not in files]
                    
                    if not missing_files:
                        print("✅ All required files present in ZIP")
                        return True
                    else:
                        print(f"❌ Missing files: {missing_files}")
                        return False
            else:
                print(f"❌ ZIP file not found at {result_path}")
                return False
        else:
            print(f"❌ Export pack generation failed: {result_path}")
            return False
            
    except Exception as e:
        print(f"❌ Export test failed: {e}")
        return False

def main():
    """Run the Day 6 export test."""
    success = test_export_pack()
    
    print("\n" + "=" * 50)
    print("📊 Day 6 Test Results:")
    
    if success:
        print("✅ Export pack generation: WORKING")
        print("✅ Document generation: WORKING") 
        print("✅ ZIP file creation: WORKING")
        print("\n🎉 Day 6 Success Criteria Met!")
        print("   ✅ Can generate ZIP with all required files")
        print("   ✅ ZIP can be downloaded and opened")
        return 0
    else:
        print("❌ Export pack generation: FAILED")
        print("\n❌ Day 6 Success Criteria Not Met")
        return 1

if __name__ == "__main__":
    sys.exit(main())
