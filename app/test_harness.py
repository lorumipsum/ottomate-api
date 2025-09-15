"""
Test Harness for OttoMate API.
Accepts sample payloads, simulates webhook calls, and records test results.
"""

import json
import time
import logging
import requests
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"

@dataclass
class TestPayload:
    """Sample payload for testing."""
    id: str
    name: str
    description: str
    data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    created_at: float = 0.0

@dataclass
class TestResult:
    """Result of a test execution."""
    id: str
    payload_id: str
    status: TestStatus
    execution_time: float
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    webhook_url: Optional[str] = None
    created_at: float = 0.0

class TestHarness:
    """Manages test execution for blueprints."""
    
    def __init__(self):
        self.payloads: Dict[str, TestPayload] = {}
        self.results: Dict[str, TestResult] = {}
        
    def add_payload(self, name: str, description: str, data: Dict[str, Any], 
                   expected_output: Optional[Dict[str, Any]] = None) -> str:
        """Add a sample payload for testing."""
        payload_id = str(uuid.uuid4())
        
        payload = TestPayload(
            id=payload_id,
            name=name,
            description=description,
            data=data,
            expected_output=expected_output,
            created_at=time.time()
        )
        
        self.payloads[payload_id] = payload
        logger.info(f"Added test payload: {name} ({payload_id})")
        return payload_id
    
    def get_payload(self, payload_id: str) -> Optional[TestPayload]:
        """Get a test payload by ID."""
        return self.payloads.get(payload_id)
    
    def list_payloads(self) -> List[TestPayload]:
        """List all test payloads."""
        return list(self.payloads.values())
    
    def run_test(self, payload_id: str, webhook_url: Optional[str] = None) -> str:
        """Run a test with the specified payload."""
        payload = self.get_payload(payload_id)
        if not payload:
            raise ValueError(f"Payload {payload_id} not found")
        
        result_id = str(uuid.uuid4())
        
        # Create initial result
        result = TestResult(
            id=result_id,
            payload_id=payload_id,
            status=TestStatus.RUNNING,
            execution_time=0.0,
            webhook_url=webhook_url,
            created_at=time.time()
        )
        
        self.results[result_id] = result
        
        try:
            start_time = time.time()
            
            if webhook_url:
                # Simulate webhook call
                success, response_data, error = self._simulate_webhook_call(webhook_url, payload.data)
            else:
                # Simulate local processing
                success, response_data, error = self._simulate_local_processing(payload.data)
            
            execution_time = time.time() - start_time
            
            # Update result
            result.execution_time = execution_time
            result.response_data = response_data
            
            if success:
                # Check if output matches expected (if provided)
                if payload.expected_output:
                    if self._compare_outputs(response_data, payload.expected_output):
                        result.status = TestStatus.PASSED
                    else:
                        result.status = TestStatus.FAILED
                        result.error_message = "Output does not match expected result"
                else:
                    result.status = TestStatus.PASSED
            else:
                result.status = TestStatus.FAILED
                result.error_message = error
                
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            logger.error(f"Test execution failed: {e}")
        
        self.results[result_id] = result
        return result_id
    
    def get_result(self, result_id: str) -> Optional[TestResult]:
        """Get a test result by ID."""
        return self.results.get(result_id)
    
    def list_results(self, payload_id: Optional[str] = None) -> List[TestResult]:
        """List test results, optionally filtered by payload ID."""
        results = list(self.results.values())
        
        if payload_id:
            results = [r for r in results if r.payload_id == payload_id]
        
        return sorted(results, key=lambda r: r.created_at, reverse=True)
    
    def get_test_summary(self, payload_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of test results."""
        results = self.list_results(payload_id)
        
        total = len(results)
        passed = len([r for r in results if r.status == TestStatus.PASSED])
        failed = len([r for r in results if r.status == TestStatus.FAILED])
        errors = len([r for r in results if r.status == TestStatus.ERROR])
        
        avg_execution_time = 0.0
        if results:
            avg_execution_time = sum(r.execution_time for r in results) / len(results)
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "average_execution_time": avg_execution_time
        }
    
    def _simulate_webhook_call(self, webhook_url: str, payload_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Simulate a webhook call."""
        try:
            logger.info(f"Simulating webhook call to {webhook_url}")
            
            # For demo purposes, we'll simulate different responses based on URL
            if "test" in webhook_url.lower() or "mock" in webhook_url.lower():
                # Simulate successful test webhook
                return True, {
                    "status": "success",
                    "message": "Webhook received and processed",
                    "received_data": payload_data,
                    "timestamp": time.time()
                }, None
            else:
                # Try actual HTTP call with timeout
                response = requests.post(
                    webhook_url,
                    json=payload_data,
                    timeout=10,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code < 400:
                    return True, response.json() if response.content else {"status": "success"}, None
                else:
                    return False, None, f"HTTP {response.status_code}: {response.text}"
                    
        except requests.exceptions.Timeout:
            return False, None, "Webhook call timed out"
        except requests.exceptions.ConnectionError:
            return False, None, "Could not connect to webhook URL"
        except Exception as e:
            return False, None, f"Webhook call failed: {str(e)}"
    
    def _simulate_local_processing(self, payload_data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Simulate local processing of payload."""
        try:
            # Simulate processing based on payload structure
            if "email" in payload_data:
                return True, {
                    "action": "email_processed",
                    "subject": payload_data.get("email", {}).get("subject", "Unknown"),
                    "processed_at": time.time()
                }, None
            elif "message" in payload_data:
                return True, {
                    "action": "message_processed", 
                    "content": payload_data.get("message", "Unknown"),
                    "processed_at": time.time()
                }, None
            else:
                return True, {
                    "action": "generic_processing",
                    "data_keys": list(payload_data.keys()),
                    "processed_at": time.time()
                }, None
                
        except Exception as e:
            return False, None, f"Local processing failed: {str(e)}"
    
    def _compare_outputs(self, actual: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Compare actual output with expected output."""
        try:
            # Simple comparison - in production this could be more sophisticated
            for key, expected_value in expected.items():
                if key not in actual:
                    return False
                if actual[key] != expected_value:
                    return False
            return True
        except Exception:
            return False

# Global instance
test_harness = TestHarness()
