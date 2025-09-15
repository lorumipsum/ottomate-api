import json
from pathlib import Path
from typing import Dict, Any, List
from jsonschema import Draft202012Validator
from app.lint_rules import ALL_RULES

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "blueprint.schema.json"

def validate_schema(bp: Dict[str, Any]) -> List[Dict[str, str]]:
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)
    out = []
    for e in validator.iter_errors(bp):
        path = ".".join(map(str, e.path)) or "$"
        out.append({"path": path, "message": e.message, "rule": "SCHEMA"})
    return out

def lint(bp: Dict[str, Any]) -> Dict[str, Any]:
    violations: List[Dict[str, str]] = []
    violations.extend(validate_schema(bp))
    if not violations:
        for rule in ALL_RULES:
            violations.extend(rule(bp))
    return {"ok": len(violations) == 0, "violations": violations, "count": len(violations)}
