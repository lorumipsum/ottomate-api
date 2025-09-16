#!/usr/bin/env python3
"""
Day 8 Test: Blueprint Diff functionality for OttoMate API.
Tests the blueprint comparison and diff functionality.
"""

import json
import sys
import os

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.blueprint_diff import blueprint_diff, ChangeType

def test_identical_blueprints():
    """Test that identical blueprints return no differences."""
    blueprint = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {
                    "app": "Gmail",
                    "trigger_type": "new_email"
                }
            }
        ],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint, blueprint)

    assert diff_result.is_identical == True
    assert diff_result.total_changes == 0
    assert len(diff_result.changes) == 0

def test_version_change():
    """Test detection of version changes."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    blueprint2 = {
        "version": "v2.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False
    assert diff_result.total_changes == 1
    assert diff_result.changes[0].change_type == ChangeType.MODIFIED
    assert diff_result.changes[0].path == "version"
    assert diff_result.changes[0].old_value == "v1.0"
    assert diff_result.changes[0].new_value == "v2.0"

def test_module_addition():
    """Test detection of module additions."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {}
            }
        ],
        "connections": []
    }

    blueprint2 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {}
            },
            {
                "id": "slack-action",
                "type": "action",
                "name": "Send Slack Message",
                "params": {
                    "channel": "#alerts"
                }
            }
        ],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False
    assert diff_result.summary["added"] == 1

    # Find the module addition change
    module_changes = [c for c in diff_result.changes if c.path == "modules.slack-action"]
    assert len(module_changes) == 1
    assert module_changes[0].change_type == ChangeType.ADDED

def test_module_removal():
    """Test detection of module removal."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {}
            },
            {
                "id": "slack-action",
                "type": "action",
                "name": "Send Slack Message",
                "params": {}
            }
        ],
        "connections": []
    }

    blueprint2 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {}
            }
        ],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False
    assert diff_result.summary["removed"] == 1

    # Find the module removal change
    module_changes = [c for c in diff_result.changes if c.path == "modules.slack-action"]
    assert len(module_changes) == 1
    assert module_changes[0].change_type == ChangeType.REMOVED

def test_parameter_changes():
    """Test detection of parameter changes within modules."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "slack-action",
                "type": "action",
                "name": "Send Slack Message",
                "params": {
                    "channel": "#alerts",
                    "message": "Hello World"
                }
            }
        ],
        "connections": []
    }

    blueprint2 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {
                "id": "slack-action",
                "type": "action",
                "name": "Send Slack Message",
                "params": {
                    "channel": "#notifications",  # Changed
                    "message": "Hello World",
                    "username": "Bot"  # Added
                }
            }
        ],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False
    assert diff_result.summary["modified"] >= 1
    assert diff_result.summary["added"] >= 1

    # Check for parameter changes
    param_changes = [c for c in diff_result.changes if "params" in c.path]
    assert len(param_changes) >= 2  # Channel change + username addition

def test_connection_changes():
    """Test detection of connection changes."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {"id": "gmail-trigger", "type": "trigger", "name": "Gmail", "params": {}},
            {"id": "slack-action", "type": "action", "name": "Slack", "params": {}}
        ],
        "connections": [
            {"from": "gmail-trigger", "to": "slack-action"}
        ]
    }

    blueprint2 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [
            {"id": "gmail-trigger", "type": "trigger", "name": "Gmail", "params": {}},
            {"id": "slack-action", "type": "action", "name": "Slack", "params": {}},
            {"id": "webhook-action", "type": "action", "name": "Webhook", "params": {}}
        ],
        "connections": [
            {"from": "gmail-trigger", "to": "slack-action"},
            {"from": "slack-action", "to": "webhook-action"}  # New connection
        ]
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False

    # Check for connection addition
    connection_changes = [c for c in diff_result.changes if "connections" in c.path]
    assert any(c.change_type == ChangeType.ADDED for c in connection_changes)

def test_human_readable_format():
    """Test human-readable diff formatting."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    blueprint2 = {
        "version": "v2.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)
    human_readable = blueprint_diff.format_diff_human_readable(diff_result)

    assert "Blueprint Diff Summary:" in human_readable
    assert "Total changes: 1" in human_readable
    assert "Modified: 1" in human_readable
    assert "Changed version from 'v1.0' to 'v2.0'" in human_readable

def test_json_format():
    """Test JSON diff formatting."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    blueprint2 = {
        "version": "v2.0",
        "triggerId": "gmail-trigger",
        "modules": [],
        "connections": []
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)
    json_diff = blueprint_diff.format_diff_json(diff_result)

    assert json_diff["is_identical"] == False
    assert json_diff["total_changes"] == 1
    assert json_diff["summary"]["modified"] == 1
    assert len(json_diff["changes"]) == 1
    assert json_diff["changes"][0]["type"] == "modified"
    assert json_diff["changes"][0]["path"] == "version"

def test_complex_blueprint_diff():
    """Test a complex diff with multiple types of changes."""
    blueprint1 = {
        "version": "v1.0",
        "triggerId": "gmail-trigger",
        "credentials": ["gmail-cred"],
        "policies": {
            "backoff": False,
            "rateLimitRPS": 100
        },
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {
                    "app": "Gmail",
                    "filter": "important"
                }
            },
            {
                "id": "old-module",
                "type": "action",
                "name": "Old Module",
                "params": {}
            }
        ],
        "connections": [
            {"from": "gmail-trigger", "to": "old-module"}
        ]
    }

    blueprint2 = {
        "version": "v2.0",  # Modified
        "triggerId": "gmail-trigger",
        "credentials": ["gmail-cred", "slack-cred"],  # Added
        "policies": {
            "backoff": True,  # Modified
            "rateLimitRPS": 100,
            "timeout": 30  # Added
        },
        "modules": [
            {
                "id": "gmail-trigger",
                "type": "trigger",
                "name": "Gmail New Email",
                "params": {
                    "app": "Gmail",
                    "filter": "all"  # Modified
                }
            },
            # old-module removed
            {
                "id": "new-module",  # Added
                "type": "action",
                "name": "New Module",
                "params": {
                    "setting": "value"
                }
            }
        ],
        "connections": [
            {"from": "gmail-trigger", "to": "new-module"}  # Modified connection
        ]
    }

    diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

    assert diff_result.is_identical == False
    assert diff_result.total_changes > 5  # Should have many changes
    assert diff_result.summary["added"] > 0
    assert diff_result.summary["removed"] > 0
    assert diff_result.summary["modified"] > 0

if __name__ == "__main__":
    print("Running Day 8 Blueprint Diff Tests...")

    # Run each test function
    test_functions = [
        test_identical_blueprints,
        test_version_change,
        test_module_addition,
        test_module_removal,
        test_parameter_changes,
        test_connection_changes,
        test_human_readable_format,
        test_json_format,
        test_complex_blueprint_diff
    ]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            print(f"  Running {test_func.__name__}...")
            test_func()
            print(f"    ✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"    ✗ FAILED: {e}")
            failed += 1

    print(f"\nTest Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All Day 8 Blueprint Diff tests passed!")
    else:
        print("❌ Some tests failed.")
        exit(1)