from typing import List, Dict, Any
import re

Violation = Dict[str, str]

def _v(path: str, msg: str, rule: str) -> Violation:
    return {"path": path, "message": msg, "rule": rule}

def rule_01_required_fields_make(bp: Dict[str, Any]) -> List[Violation]:
    """Check required fields for Make.com blueprint format"""
    v: List[Violation] = []
    required = ["version", "triggerId", "modules", "connections"]
    for field in required:
        if field not in bp:
            v.append(_v(field, f"Required field '{field}' is missing", "M01"))
    return v

def rule_02_valid_version_make(bp: Dict[str, Any]) -> List[Violation]:
    """Check version follows Make.com pattern (v1.0, v2.1, etc.)"""
    v: List[Violation] = []
    version = bp.get("version", "")
    if not re.match(r'^v\d+(\.\d+)?$', version):
        v.append(_v("version", "Version must follow Make.com pattern (e.g., v1.0, v2.1)", "M02"))
    return v

def rule_03_valid_trigger_id(bp: Dict[str, Any]) -> List[Violation]:
    """Check triggerId is valid"""
    v: List[Violation] = []
    trigger_id = bp.get("triggerId", "")
    if not trigger_id or len(trigger_id) < 1:
        v.append(_v("triggerId", "triggerId must be a non-empty string", "M03"))
    return v

def rule_04_modules_structure(bp: Dict[str, Any]) -> List[Violation]:
    """Check modules array structure"""
    v: List[Violation] = []
    modules = bp.get("modules", [])
    
    if not isinstance(modules, list):
        v.append(_v("modules", "modules must be an array", "M04"))
        return v
    
    if len(modules) == 0:
        v.append(_v("modules", "modules array cannot be empty", "M04"))
        return v
    
    # Check each module has required fields
    for i, module in enumerate(modules):
        if not isinstance(module, dict):
            v.append(_v(f"modules[{i}]", "Each module must be an object", "M04"))
            continue
            
        required_fields = ["id", "type", "name", "params"]
        for field in required_fields:
            if field not in module:
                v.append(_v(f"modules[{i}].{field}", f"Module missing required field '{field}'", "M04"))
    
    return v

# All Make.com format lint rules
ALL_MAKE_RULES = [
    rule_01_required_fields_make,
    rule_02_valid_version_make,
    rule_03_valid_trigger_id,
    rule_04_modules_structure,
]
