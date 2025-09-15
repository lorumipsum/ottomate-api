"""
Export Pack Generator for OttoMate API.
Creates ZIP files with blueprint and documentation.
"""

import json
import zipfile
import tempfile
import os
from typing import Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from app.document_generator import document_generator
from app.lint_runner import lint

class ExportPackGenerator:
    """Generates export packs with blueprint and documentation."""
    
    def generate_export_pack(self, blueprint: Dict[str, Any], brief: str, job_id: str = None) -> Tuple[bool, str]:
        """
        Generate a complete export pack ZIP file.
        
        Returns:
            Tuple of (success: bool, file_path_or_error: str)
        """
        try:
            # Create temporary directory for files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Generate all documents
                self._create_blueprint_json(blueprint, temp_path)
                self._create_proposal_md(blueprint, brief, temp_path)
                self._create_runbook_md(blueprint, brief, temp_path)
                self._create_validation_report_md(blueprint, temp_path)
                
                # Create ZIP file
                zip_filename = f"automation_pack_{job_id or 'export'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = Path("data/exports") / zip_filename
                
                # Ensure exports directory exists
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Create the ZIP file
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_path.glob("*"):
                        zipf.write(file_path, file_path.name)
                
                return True, str(zip_path)
                
        except Exception as e:
            return False, f"Export pack generation failed: {str(e)}"
    
    def _create_blueprint_json(self, blueprint: Dict[str, Any], temp_path: Path):
        """Create blueprint.json file."""
        blueprint_file = temp_path / "blueprint.json"
        with open(blueprint_file, 'w') as f:
            json.dump(blueprint, f, indent=2)
    
    def _create_proposal_md(self, blueprint: Dict[str, Any], brief: str, temp_path: Path):
        """Create proposal.md file."""
        proposal_content = document_generator.generate_proposal(blueprint, brief)
        proposal_file = temp_path / "proposal.md"
        with open(proposal_file, 'w') as f:
            f.write(proposal_content)
    
    def _create_runbook_md(self, blueprint: Dict[str, Any], brief: str, temp_path: Path):
        """Create runbook.md file."""
        runbook_content = document_generator.generate_runbook(blueprint, brief)
        runbook_file = temp_path / "runbook.md"
        with open(runbook_file, 'w') as f:
            f.write(runbook_content)
    
    def _create_validation_report_md(self, blueprint: Dict[str, Any], temp_path: Path):
        """Create validation_report.md file."""
        # Run validation
        lint_result = lint(blueprint)
        
        validation_content = document_generator.generate_validation_report(blueprint, lint_result)
        validation_file = temp_path / "validation_report.md"
        with open(validation_file, 'w') as f:
            f.write(validation_content)

# Global instance
export_pack_generator = ExportPackGenerator()
