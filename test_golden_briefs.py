#!/usr/bin/env python3
"""
Test script to validate Golden Briefs against schema and lint rules.
"""

import json
import sys
from pathlib import Path
from app.lint_runner import lint

def test_golden_brief(filepath):
    """Test a single Golden Brief file."""
    print(f"\n🧪 Testing: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            blueprint = json.load(f)
        
        # Run lint validation
        result = lint(blueprint)
        
        print(f"✅ Loaded successfully")
        print(f"📊 Lint result: {'PASS' if result['ok'] else 'FAIL'}")
        print(f"🔍 Violations: {result['count']}")
        
        if result['violations']:
            print("📝 Issues found:")
            for violation in result['violations']:
                print(f"   - {violation['rule']}: {violation['message']} (path: {violation['path']})")
        
        return result['ok']
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run tests on all Golden Brief files."""
    print("🚀 Golden Briefs Validation Test")
    print("=" * 50)
    
    test_files = [
        "tests/fixtures/gb-1.json",
        "tests/fixtures/gb-2.json", 
        "tests/fixtures/gb-1-make.json",
        "tests/fixtures/gb-make-compliant.json"
    ]
    
    results = []
    for filepath in test_files:
        if Path(filepath).exists():
            results.append(test_golden_brief(filepath))
        else:
            print(f"\n⚠️  File not found: {filepath}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📈 Summary:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed >= 1:
        print("🎉 At least one Golden Brief is working!")
        return 0
    else:
        print("⚠️  No Golden Briefs are passing. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
