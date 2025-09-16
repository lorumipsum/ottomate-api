"""
Blueprint Diff functionality for OttoMate API.
Compares two blueprints and provides detailed difference analysis.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Types of changes in blueprint diff."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

@dataclass
class Change:
    """Represents a single change in blueprint diff."""
    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    description: str = ""

@dataclass
class DiffResult:
    """Result of blueprint comparison."""
    changes: List[Change]
    summary: Dict[str, int]
    is_identical: bool
    total_changes: int

class BlueprintDiff:
    """Provides blueprint comparison and diff functionality."""

    def __init__(self):
        pass

    def compare_blueprints(self, blueprint1: Dict[str, Any], blueprint2: Dict[str, Any]) -> DiffResult:
        """
        Compare two blueprints and return detailed diff.

        Args:
            blueprint1: The first blueprint (often the "old" version)
            blueprint2: The second blueprint (often the "new" version)

        Returns:
            DiffResult containing all detected changes
        """
        changes = []

        # Compare top-level properties
        changes.extend(self._compare_top_level(blueprint1, blueprint2))

        # Compare modules
        changes.extend(self._compare_modules(
            blueprint1.get("modules", []),
            blueprint2.get("modules", [])
        ))

        # Compare connections
        changes.extend(self._compare_connections(
            blueprint1.get("connections", []),
            blueprint2.get("connections", [])
        ))

        # Compare policies
        changes.extend(self._compare_policies(
            blueprint1.get("policies", {}),
            blueprint2.get("policies", {})
        ))

        # Compare credentials
        changes.extend(self._compare_credentials(
            blueprint1.get("credentials", []),
            blueprint2.get("credentials", [])
        ))

        # Calculate summary
        summary = self._calculate_summary(changes)
        is_identical = len(changes) == 0

        return DiffResult(
            changes=changes,
            summary=summary,
            is_identical=is_identical,
            total_changes=len(changes)
        )

    def _compare_top_level(self, bp1: Dict[str, Any], bp2: Dict[str, Any]) -> List[Change]:
        """Compare top-level blueprint properties."""
        changes = []
        top_level_fields = ["version", "triggerId"]

        for field in top_level_fields:
            old_val = bp1.get(field)
            new_val = bp2.get(field)

            if old_val != new_val:
                if old_val is None:
                    changes.append(Change(
                        path=field,
                        change_type=ChangeType.ADDED,
                        new_value=new_val,
                        description=f"Added {field}: {new_val}"
                    ))
                elif new_val is None:
                    changes.append(Change(
                        path=field,
                        change_type=ChangeType.REMOVED,
                        old_value=old_val,
                        description=f"Removed {field}: {old_val}"
                    ))
                else:
                    changes.append(Change(
                        path=field,
                        change_type=ChangeType.MODIFIED,
                        old_value=old_val,
                        new_value=new_val,
                        description=f"Changed {field} from '{old_val}' to '{new_val}'"
                    ))

        return changes

    def _compare_modules(self, modules1: List[Dict], modules2: List[Dict]) -> List[Change]:
        """Compare blueprint modules."""
        changes = []

        # Create lookup dictionaries by module ID
        modules1_by_id = {mod.get("id"): mod for mod in modules1}
        modules2_by_id = {mod.get("id"): mod for mod in modules2}

        all_module_ids = set(modules1_by_id.keys()) | set(modules2_by_id.keys())

        for module_id in all_module_ids:
            mod1 = modules1_by_id.get(module_id)
            mod2 = modules2_by_id.get(module_id)

            if mod1 is None:
                # Module added
                changes.append(Change(
                    path=f"modules.{module_id}",
                    change_type=ChangeType.ADDED,
                    new_value=mod2,
                    description=f"Added module '{module_id}' ({mod2.get('name', 'Unknown')})"
                ))
            elif mod2 is None:
                # Module removed
                changes.append(Change(
                    path=f"modules.{module_id}",
                    change_type=ChangeType.REMOVED,
                    old_value=mod1,
                    description=f"Removed module '{module_id}' ({mod1.get('name', 'Unknown')})"
                ))
            else:
                # Compare module properties
                changes.extend(self._compare_module_properties(module_id, mod1, mod2))

        return changes

    def _compare_module_properties(self, module_id: str, mod1: Dict, mod2: Dict) -> List[Change]:
        """Compare properties of a single module."""
        changes = []
        module_fields = ["type", "name", "external", "authRequired", "throttled", "iterates", "hasLimiter", "hasErrorHandler"]

        for field in module_fields:
            old_val = mod1.get(field)
            new_val = mod2.get(field)

            if old_val != new_val:
                path = f"modules.{module_id}.{field}"
                if old_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.ADDED,
                        new_value=new_val,
                        description=f"Added {field} to module '{module_id}': {new_val}"
                    ))
                elif new_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.REMOVED,
                        old_value=old_val,
                        description=f"Removed {field} from module '{module_id}': {old_val}"
                    ))
                else:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.MODIFIED,
                        old_value=old_val,
                        new_value=new_val,
                        description=f"Changed {field} in module '{module_id}' from '{old_val}' to '{new_val}'"
                    ))

        # Compare params
        changes.extend(self._compare_params(module_id, mod1.get("params", {}), mod2.get("params", {})))

        # Compare mappings
        changes.extend(self._compare_mappings(module_id, mod1.get("mappings", []), mod2.get("mappings", [])))

        return changes

    def _compare_params(self, module_id: str, params1: Dict, params2: Dict) -> List[Change]:
        """Compare module parameters."""
        changes = []
        all_param_keys = set(params1.keys()) | set(params2.keys())

        for param_key in all_param_keys:
            old_val = params1.get(param_key)
            new_val = params2.get(param_key)

            if old_val != new_val:
                path = f"modules.{module_id}.params.{param_key}"
                if old_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.ADDED,
                        new_value=new_val,
                        description=f"Added parameter '{param_key}' to module '{module_id}': {new_val}"
                    ))
                elif new_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.REMOVED,
                        old_value=old_val,
                        description=f"Removed parameter '{param_key}' from module '{module_id}': {old_val}"
                    ))
                else:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.MODIFIED,
                        old_value=old_val,
                        new_value=new_val,
                        description=f"Changed parameter '{param_key}' in module '{module_id}' from '{old_val}' to '{new_val}'"
                    ))

        return changes

    def _compare_mappings(self, module_id: str, mappings1: List, mappings2: List) -> List[Change]:
        """Compare module mappings."""
        changes = []

        # Simple comparison - could be enhanced to match by field name
        if len(mappings1) != len(mappings2):
            changes.append(Change(
                path=f"modules.{module_id}.mappings",
                change_type=ChangeType.MODIFIED,
                old_value=mappings1,
                new_value=mappings2,
                description=f"Changed mappings count in module '{module_id}' from {len(mappings1)} to {len(mappings2)}"
            ))
        elif mappings1 != mappings2:
            changes.append(Change(
                path=f"modules.{module_id}.mappings",
                change_type=ChangeType.MODIFIED,
                old_value=mappings1,
                new_value=mappings2,
                description=f"Modified mappings in module '{module_id}'"
            ))

        return changes

    def _compare_connections(self, connections1: List, connections2: List) -> List[Change]:
        """Compare blueprint connections."""
        changes = []

        # Convert to sets of tuples for comparison
        conn1_set = {(conn.get("from"), conn.get("to")) for conn in connections1}
        conn2_set = {(conn.get("from"), conn.get("to")) for conn in connections2}

        # Find added connections
        added = conn2_set - conn1_set
        for from_module, to_module in added:
            changes.append(Change(
                path=f"connections.{from_module}->{to_module}",
                change_type=ChangeType.ADDED,
                new_value={"from": from_module, "to": to_module},
                description=f"Added connection from '{from_module}' to '{to_module}'"
            ))

        # Find removed connections
        removed = conn1_set - conn2_set
        for from_module, to_module in removed:
            changes.append(Change(
                path=f"connections.{from_module}->{to_module}",
                change_type=ChangeType.REMOVED,
                old_value={"from": from_module, "to": to_module},
                description=f"Removed connection from '{from_module}' to '{to_module}'"
            ))

        return changes

    def _compare_policies(self, policies1: Dict, policies2: Dict) -> List[Change]:
        """Compare blueprint policies."""
        changes = []
        all_policy_keys = set(policies1.keys()) | set(policies2.keys())

        for policy_key in all_policy_keys:
            old_val = policies1.get(policy_key)
            new_val = policies2.get(policy_key)

            if old_val != new_val:
                path = f"policies.{policy_key}"
                if old_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.ADDED,
                        new_value=new_val,
                        description=f"Added policy '{policy_key}': {new_val}"
                    ))
                elif new_val is None:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.REMOVED,
                        old_value=old_val,
                        description=f"Removed policy '{policy_key}': {old_val}"
                    ))
                else:
                    changes.append(Change(
                        path=path,
                        change_type=ChangeType.MODIFIED,
                        old_value=old_val,
                        new_value=new_val,
                        description=f"Changed policy '{policy_key}' from '{old_val}' to '{new_val}'"
                    ))

        return changes

    def _compare_credentials(self, creds1: List, creds2: List) -> List[Change]:
        """Compare blueprint credentials."""
        changes = []

        creds1_set = set(creds1)
        creds2_set = set(creds2)

        # Find added credentials
        added = creds2_set - creds1_set
        for cred in added:
            changes.append(Change(
                path=f"credentials.{cred}",
                change_type=ChangeType.ADDED,
                new_value=cred,
                description=f"Added credential: {cred}"
            ))

        # Find removed credentials
        removed = creds1_set - creds2_set
        for cred in removed:
            changes.append(Change(
                path=f"credentials.{cred}",
                change_type=ChangeType.REMOVED,
                old_value=cred,
                description=f"Removed credential: {cred}"
            ))

        return changes

    def _calculate_summary(self, changes: List[Change]) -> Dict[str, int]:
        """Calculate summary statistics from changes."""
        summary = {
            "total": len(changes),
            "added": 0,
            "removed": 0,
            "modified": 0
        }

        for change in changes:
            if change.change_type == ChangeType.ADDED:
                summary["added"] += 1
            elif change.change_type == ChangeType.REMOVED:
                summary["removed"] += 1
            elif change.change_type == ChangeType.MODIFIED:
                summary["modified"] += 1

        return summary

    def format_diff_human_readable(self, diff_result: DiffResult) -> str:
        """Format diff result as human-readable text."""
        if diff_result.is_identical:
            return "The blueprints are identical."

        lines = [
            f"Blueprint Diff Summary:",
            f"  Total changes: {diff_result.total_changes}",
            f"  Added: {diff_result.summary['added']}",
            f"  Removed: {diff_result.summary['removed']}",
            f"  Modified: {diff_result.summary['modified']}",
            "",
            "Changes:"
        ]

        for change in diff_result.changes:
            symbol = {
                ChangeType.ADDED: "+",
                ChangeType.REMOVED: "-",
                ChangeType.MODIFIED: "~"
            }.get(change.change_type, "?")

            lines.append(f"  {symbol} {change.description}")

        return "\n".join(lines)

    def format_diff_json(self, diff_result: DiffResult) -> Dict[str, Any]:
        """Format diff result as structured JSON."""
        return {
            "is_identical": diff_result.is_identical,
            "summary": diff_result.summary,
            "total_changes": diff_result.total_changes,
            "changes": [
                {
                    "path": change.path,
                    "type": change.change_type.value,
                    "description": change.description,
                    "old_value": change.old_value,
                    "new_value": change.new_value
                }
                for change in diff_result.changes
            ]
        }

# Global instance
blueprint_diff = BlueprintDiff()