from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Any, Dict, List
import json, pathlib
from jsonschema import Draft202012Validator, exceptions as js_ex
from lints import ALL_RULES

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

SCHEMA_PATH = pathlib.Path(__file__).parent / "blueprint.schema.json"
SCHEMA_OBJ = json.loads(SCHEMA_PATH.read_text())

class LintResponse(BaseModel):
    valid: bool
    schema_errors: List[str] = []
    rule_failures: List[str] = []

@app.get("/schema")
def get_schema():
    return SCHEMA_OBJ

@app.post("/lint", response_model=LintResponse)
def lint_blueprint(blueprint: Dict[str, Any] = Body(...)):
    # 1) Schema validation
    schema_errors: List[str] = []
    try:
        Draft202012Validator(SCHEMA_OBJ).validate(blueprint)
    except js_ex.ValidationError:
        v = Draft202012Validator(SCHEMA_OBJ)
        schema_errors = [f"{err.message} at {list(err.path)}" for err in v.iter_errors(blueprint)]
    # 2) Rules (only if schema clean)
    rule_failures: List[str] = []
    if not schema_errors:
        for rule in ALL_RULES:
            rule_failures.extend(rule(blueprint))
    return LintResponse(
        valid=(not schema_errors and not rule_failures),
        schema_errors=schema_errors,
        rule_failures=rule_failures
    )
