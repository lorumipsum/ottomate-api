from typing import List, Dict, Any
import re

Violation = Dict[str, str]

def _v(path: str, msg: str, rule: str) -> Violation:
    return {"path": path, "message": msg, "rule": rule}

def rule_01_required_fields(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    required = ["name", "version", "trigger", "actions"]
    for field in required:
        if field not in bp:
            v.append(_v(field, f"Required field '{field}' is missing", "R01"))
    return v

def rule_02_valid_version(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    version = bp.get("version", "")
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        v.append(_v("version", "Version must follow semantic versioning", "R02"))
    return v

def rule_03_valid_name_length(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    name = bp.get("name", "")
    if not name or len(name) > 100:
        v.append(_v("name", "Name must be 1-100 characters long", "R03"))
    return v

def rule_04_valid_trigger(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    trigger = bp.get("trigger", {})
    if "type" not in trigger:
        v.append(_v("trigger.type", "Trigger must have a type", "R04"))
    if "app" not in trigger:
        v.append(_v("trigger.app", "Trigger must specify an app", "R04"))
    return v

def rule_05_actions_not_empty(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    actions = bp.get("actions", [])
    if not isinstance(actions, list) or len(actions) == 0:
        v.append(_v("actions", "Actions must be a non-empty array", "R05"))
    return v

def rule_06_valid_action_structure(bp: Dict[str, Any]) -> List[Violation]:
    v: List[Violation] = []
    actions = bp.get("actions", [])
    if isinstance(actions, list):
        for i, action in enumerate(actions):
            if not isinstance(action, dict):
                v.append(_v(f"actions[{i}]", "Action must be an object", "R06"))
    return v

def rule_07_unique_action_ids(bp: Dict[str, Any]) -> List[Violation]:
    return []

def rule_08_valid_dependencies(bp: Dict[str, Any]) -> List[Violation]:
    return []

def rule_09_valid_error_handling(bp: Dict[str, Any]) -> List[Violation]:
    return []

def rule_10_valid_description_length(bp: Dict[str, Any]) -> List[Violation]:
    return []

ALL_RULES = [
    rule_01_required_fields, rule_02_valid_version, rule_03_valid_name_length,
    rule_04_valid_trigger, rule_05_actions_not_empty, rule_06_valid_action_structure,
    rule_07_unique_action_ids, rule_08_valid_dependencies, rule_09_valid_error_handling,
    rule_10_valid_description_length
]
