from typing import List, Dict, Any
import re

def rule_unique_module_ids(bp: Dict[str, Any]) -> List[str]:
    ids = [m.get("id") for m in bp.get("modules", [])]
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    return [f"Duplicate module id: {d}" for d in dupes]

def rule_no_orphan_connections(bp: Dict[str, Any]) -> List[str]:
    ids = {m.get("id") for m in bp.get("modules", [])}
    errs = []
    for c in bp.get("connections", []):
        if c.get("from") not in ids:
            errs.append(f"Connection from unknown module: {c.get('from')}")
        if c.get("to") not in ids:
            errs.append(f"Connection to unknown module: {c.get('to')}")
    return errs

def rule_name_present(bp: Dict[str, Any]) -> List[str]:
    return [] if bp.get("name") else ["Blueprint name missing"]

def rule_min_one_connection(bp: Dict[str, Any]) -> List[str]:
    return [] if len(bp.get("connections", [])) >= 1 else ["At least one connection required"]

def rule_module_types_present(bp: Dict[str, Any]) -> List[str]:
    errs = []
    for m in bp.get("modules", []):
        if not m.get("type"):
            errs.append(f"Module {m.get('id')} missing type")
    return errs

def rule_config_is_object(bp: Dict[str, Any]) -> List[str]:
    errs = []
    for m in bp.get("modules", []):
        if not isinstance(m.get("config"), dict):
            errs.append(f"Module {m.get('id')} config must be object")
    return errs

def rule_id_format(bp: Dict[str, Any]) -> List[str]:
    errs=[]
    for m in bp.get("modules", []):
        mid = m.get("id","")
        if not re.fullmatch(r"[A-Za-z0-9_\-]{3,64}", mid or ""):
            errs.append(f"Module id invalid: {mid}")
    return errs

def rule_no_cycles_trivial(bp: Dict[str, Any]) -> List[str]:
    pairs=set((c.get("from"), c.get("to")) for c in bp.get("connections", []))
    errs=[]
    for f,t in pairs:
        if f==t:
            errs.append(f"Self-loop not allowed: {f}")
        if (t,f) in pairs and f!=t:
            errs.append(f"2-node cycle between {f} and {t}")
    return errs

def rule_entrypoint_exists(bp: Dict[str, Any]) -> List[str]:
    for m in bp.get("modules", []):
        if m.get("type","").lower()=="trigger" or m.get("config",{}).get("trigger") is True:
            return []
    return ["No trigger/entrypoint module found"]

def rule_output_exists(bp: Dict[str, Any]) -> List[str]:
    outs={"http_response","datastore_write","email_send","webhook_reply"}
    for m in bp.get("modules", []):
        if m.get("type","").lower() in outs:
            return []
    return ["No obvious output/sink module found"]

ALL_RULES=[
    rule_unique_module_ids,
    rule_no_orphan_connections,
    rule_name_present,
    rule_min_one_connection,
    rule_module_types_present,
    rule_config_is_object,
    rule_id_format,
    rule_no_cycles_trivial,
    rule_entrypoint_exists,
    rule_output_exists,
]
