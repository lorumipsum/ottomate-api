#!/usr/bin/env python3
"""
End-to-end test for Golden Briefs with real OpenAI generation.
Tests the complete flow: brief → generate → lint → export in ≤3 min.
"""

import json
import time
import sys
import os
from typing import Dict, Any

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.blueprint_generator import blueprint_generator
from app.brief_manager import brief_manager
from app.job_runner import job_runner
from app.export_pack import export_pack_generator
from app.lint_runner import lint

class GoldenBriefTester:
    """Test Golden Briefs end-to-end with real LLM generation."""

    def __init__(self):
        self.results = {}

    def test_gb1_hubspot_to_sheets_slack(self):
        """
        GB-1: HubSpot new contact → Google Sheets append + Slack notify.
        """
        brief_content = """
        When a new contact is created in HubSpot, I need to:
        1. Append the contact details (email, first_name, last_name) to a Google Sheets document
        2. Send a notification to the #sales-alerts Slack channel with the new contact information

        The Google Sheet should be updated with email, first_name, and last_name in separate columns.
        The Slack message should include the full name and email address.
        """

        return self._test_brief("GB-1: HubSpot → Sheets + Slack", brief_content, {
            "expected_apps": ["HubSpot", "Google Sheets", "Slack"],
            "expected_modules": 3,  # Trigger + 2 actions
            "expected_connections": 2  # HubSpot → Sheets, HubSpot → Slack (or chain)
        })

    def test_gb2_typeform_to_airtable_gmail(self):
        """
        GB-2: Typeform submission → Airtable create + Gmail draft reply.
        """
        brief_content = """
        When someone submits a Typeform response, I need to:
        1. Create a new record in Airtable with the form submission data (name, email, interest)
        2. Create a draft reply email in Gmail addressed to the submitter

        The Airtable record should capture the name, email, and their area of interest.
        The Gmail draft should be personalized with their name and a template response about their interest.
        """

        return self._test_brief("GB-2: Typeform → Airtable + Gmail", brief_content, {
            "expected_apps": ["Typeform", "Airtable", "Gmail"],
            "expected_modules": 3,  # Trigger + 2 actions
            "expected_connections": 2  # Typeform → Airtable, Typeform → Gmail (or chain)
        })

    def _test_brief(self, test_name: str, brief_content: str, expectations: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single brief end-to-end."""
        print(f"\n🧪 Testing {test_name}")
        print("=" * 60)

        start_time = time.time()
        test_result = {
            "test_name": test_name,
            "success": False,
            "duration_seconds": 0,
            "steps": {},
            "errors": [],
            "blueprint": None,
            "export_path": None
        }

        try:
            # Step 1: Create brief
            step_start = time.time()
            brief = brief_manager.create_brief(brief_content)
            test_result["steps"]["create_brief"] = {
                "success": True,
                "duration": time.time() - step_start,
                "brief_id": brief.id
            }
            print(f"✅ Brief created: {brief.id}")

            # Step 2: Generate blueprint
            step_start = time.time()
            job = brief_manager.create_job(brief.id)

            if not job:
                raise Exception("Failed to create job")

            job_success = job_runner.start_job(job.id)
            if not job_success:
                raise Exception("Failed to start job")

            # Wait for job completion (with timeout)
            timeout = 120  # 2 minutes max for generation
            poll_start = time.time()
            updated_job = None

            while True:
                updated_job = brief_manager.get_job(job.id)
                if updated_job is None:
                    raise Exception(f"Job {job.id} disappeared or could not be loaded")

                if updated_job.status.value in ["completed", "failed"]:
                    break

                if time.time() - poll_start > timeout:
                    raise Exception("Job generation timed out")

                time.sleep(1)  # Poll every second

            generation_duration = time.time() - step_start
            test_result["steps"]["generate_blueprint"] = {
                "success": updated_job.status.value == "completed",
                "duration": generation_duration,
                "job_id": job.id,
                "status": updated_job.status.value
            }

            if updated_job.status.value != "completed":
                raise Exception(f"Job failed: {updated_job.error}")

            blueprint = updated_job.result["blueprint"]
            test_result["blueprint"] = blueprint
            print(f"✅ Blueprint generated in {generation_duration:.2f}s")

            # Step 3: Validate blueprint
            step_start = time.time()
            lint_result = lint(blueprint)
            test_result["steps"]["validate_blueprint"] = {
                "success": lint_result["ok"],
                "duration": time.time() - step_start,
                "violations": lint_result.get("violations", [])
            }

            if not lint_result["ok"]:
                print(f"⚠️  Blueprint validation warnings: {len(lint_result['violations'])} violations")
                for violation in lint_result["violations"]:
                    print(f"   - {violation}")
            else:
                print("✅ Blueprint validation passed")

            # Step 4: Verify expectations
            step_start = time.time()
            verification_result = self._verify_expectations(blueprint, expectations)
            test_result["steps"]["verify_expectations"] = {
                "success": verification_result["success"],
                "duration": time.time() - step_start,
                "details": verification_result
            }

            if verification_result["success"]:
                print("✅ Blueprint meets expectations")
            else:
                print(f"⚠️  Blueprint expectations not fully met:")
                for issue in verification_result["issues"]:
                    print(f"   - {issue}")

            # Step 5: Generate export pack
            step_start = time.time()
            export_success, export_result = export_pack_generator.generate_export_pack(
                blueprint, brief_content, job.id
            )
            test_result["steps"]["generate_export"] = {
                "success": export_success,
                "duration": time.time() - step_start,
                "export_path": export_result if export_success else None
            }

            if export_success:
                test_result["export_path"] = export_result
                print(f"✅ Export pack generated: {export_result}")
            else:
                print(f"❌ Export generation failed: {export_result}")

            # Calculate total duration
            total_duration = time.time() - start_time
            test_result["duration_seconds"] = total_duration

            # Determine overall success
            all_steps_ok = all(step.get("success", False) for step in test_result["steps"].values())
            within_time_limit = total_duration <= 180  # 3 minutes

            test_result["success"] = all_steps_ok and within_time_limit

            print(f"\n📊 Test Results:")
            print(f"   Duration: {total_duration:.2f}s ({'✅' if within_time_limit else '❌'} ≤180s)")
            print(f"   Overall: {'✅ PASSED' if test_result['success'] else '❌ FAILED'}")

            return test_result

        except Exception as e:
            test_result["duration_seconds"] = time.time() - start_time
            test_result["errors"].append(str(e))
            print(f"❌ Test failed: {e}")
            return test_result

    def _verify_expectations(self, blueprint: Dict[str, Any], expectations: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the blueprint meets the expected criteria."""
        issues = []

        # Check module count
        actual_modules = len(blueprint.get("modules", []))
        expected_modules = expectations.get("expected_modules", 0)
        if actual_modules != expected_modules:
            issues.append(f"Expected {expected_modules} modules, got {actual_modules}")

        # Check connection count
        actual_connections = len(blueprint.get("connections", []))
        expected_connections = expectations.get("expected_connections", 0)
        if actual_connections < expected_connections:
            issues.append(f"Expected at least {expected_connections} connections, got {actual_connections}")

        # Check for expected apps
        expected_apps = expectations.get("expected_apps", [])
        module_apps = []
        for module in blueprint.get("modules", []):
            app = module.get("params", {}).get("app")
            if app:
                module_apps.append(app)

        for expected_app in expected_apps:
            if expected_app not in module_apps:
                issues.append(f"Expected app '{expected_app}' not found in modules")

        # Check for trigger module
        trigger_modules = [m for m in blueprint.get("modules", []) if m.get("type") == "trigger"]
        if not trigger_modules:
            issues.append("No trigger module found")

        # Check that triggerId matches a module
        trigger_id = blueprint.get("triggerId")
        module_ids = [m.get("id") for m in blueprint.get("modules", [])]
        if trigger_id not in module_ids:
            issues.append(f"triggerId '{trigger_id}' does not match any module ID")

        return {
            "success": len(issues) == 0,
            "issues": issues,
            "actual_modules": actual_modules,
            "actual_connections": actual_connections,
            "found_apps": module_apps
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Golden Brief tests and return summary."""
        print("🚀 Starting Golden Brief End-to-End Tests")
        print("Testing the complete flow: brief → generate → lint → export")
        print("Target: ≤3 minutes per brief")

        overall_start = time.time()

        # Run both Golden Brief tests
        gb1_result = self.test_gb1_hubspot_to_sheets_slack()
        gb2_result = self.test_gb2_typeform_to_airtable_gmail()

        total_duration = time.time() - overall_start

        # Calculate summary
        all_passed = gb1_result["success"] and gb2_result["success"]

        summary = {
            "overall_success": all_passed,
            "total_duration": total_duration,
            "gb1_result": gb1_result,
            "gb2_result": gb2_result,
            "openai_available": blueprint_generator.client is not None
        }

        print(f"\n" + "=" * 60)
        print("📊 GOLDEN BRIEF TEST SUMMARY")
        print("=" * 60)
        print(f"GB-1 (HubSpot → Sheets + Slack): {'✅ PASSED' if gb1_result['success'] else '❌ FAILED'} ({gb1_result['duration_seconds']:.1f}s)")
        print(f"GB-2 (Typeform → Airtable + Gmail): {'✅ PASSED' if gb2_result['success'] else '❌ FAILED'} ({gb2_result['duration_seconds']:.1f}s)")
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"OpenAI Available: {'✅ YES' if summary['openai_available'] else '❌ NO (using mocks)'}")
        print(f"Overall Result: {'🎉 ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        if all_passed:
            print(f"\n✅ SUCCESS: Golden Briefs are working end-to-end!")
            print(f"   Both briefs generated valid blueprints and exports")
            print(f"   Ready for Day 10 demo preparation")
        else:
            print(f"\n❌ Issues found that need attention before demo:")
            if not gb1_result["success"]:
                print(f"   GB-1 issues: {', '.join(gb1_result['errors'])}")
            if not gb2_result["success"]:
                print(f"   GB-2 issues: {', '.join(gb2_result['errors'])}")

        return summary

def main():
    """Run Golden Brief tests."""
    tester = GoldenBriefTester()

    # Check if OpenAI is configured
    if not blueprint_generator.client:
        print("⚠️  WARNING: OpenAI API not configured - using mock generation")
        print("   Set OPENAI_API_KEY environment variable for real LLM testing")
        print("   Tests will still run with mock blueprints\n")

    summary = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if summary["overall_success"] else 1)

if __name__ == "__main__":
    main()