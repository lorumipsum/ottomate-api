import os
import time
from pathlib import Path
import json
import os
from flask import Flask, request, jsonify
from app.lint_runner import lint
from app.blueprint_generator import blueprint_generator
from app.guardrails import guardrails
from app.brief_manager import brief_manager
from app.job_runner import job_runner

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/schema")
def schema():
    """Serve the Blueprint JSON Schema"""
    try:
        # Load the schema from the root directory
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'blueprint-schema.json')
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        return jsonify(schema)
    except FileNotFoundError:
        return jsonify({"error": "Blueprint schema not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in schema file"}), 500

@app.post("/lint")
def lint_endpoint():
    try:
        bp = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400
    result = lint(bp or {})
    status = 200 if result["ok"] else 422
    return jsonify(result), status

@app.post("/generate")
def generate_blueprint():
    """Generate a blueprint from a natural language brief."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400
    
    if not data or 'brief' not in data:
        return jsonify({"ok": False, "error": "Missing 'brief' field in request"}), 400
    
    brief = data['brief']
    if not brief or not brief.strip():
        return jsonify({"ok": False, "error": "Brief cannot be empty"}), 400
    
    # Check if generator is available
    if not blueprint_generator.is_available():
        return jsonify({
            "ok": False,
            "error": "Blueprint generator not available - OpenAI API key not configured"
        }), 503
    
    # Generate blueprint
    success, result = blueprint_generator.generate_blueprint(brief)
    
    if success:
        return jsonify({
            "ok": True,
            "blueprint": result["blueprint"]
        })
    else:
        return jsonify({
            "ok": False,
            "error": result["error"],
            "violations": result.get("violations", [])
        }), 400

@app.get("/usage")
def get_usage():
    """Get current usage statistics for guardrails."""
    try:
        stats = guardrails.get_usage_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/briefs")
def create_brief():
    """Create and store a new brief."""
    try:
        data = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400
    
    if not data or 'content' not in data:
        return jsonify({"ok": False, "error": "Missing 'content' field in request"}), 400
    
    content = data['content']
    if not content or not content.strip():
        return jsonify({"ok": False, "error": "Brief content cannot be empty"}), 400
    
    metadata = data.get('metadata', {})
    
    try:
        brief = brief_manager.create_brief(content, metadata)
        return jsonify({
            "ok": True,
            "brief": {
                "id": brief.id,
                "content": brief.content,
                "created_at": brief.created_at,
                "metadata": brief.metadata
            }
        }), 201
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/briefs")
def list_briefs():
    """List all briefs."""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        
        briefs = brief_manager.list_briefs(limit)
        return jsonify({
            "ok": True,
            "briefs": [
                {
                    "id": brief.id,
                    "content": brief.content,
                    "created_at": brief.created_at,
                    "metadata": brief.metadata
                }
                for brief in briefs
            ],
            "count": len(briefs)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/briefs/<brief_id>")
def get_brief(brief_id):
    """Get a specific brief by ID."""
    try:
        brief = brief_manager.get_brief(brief_id)
        if not brief:
            return jsonify({"ok": False, "error": "Brief not found"}), 404
        
        return jsonify({
            "ok": True,
            "brief": {
                "id": brief.id,
                "content": brief.content,
                "created_at": brief.created_at,
                "metadata": brief.metadata
            }
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/briefs/<brief_id>:generate")
def generate_from_brief(brief_id):
    """Generate a blueprint from a stored brief."""
    try:
        # Check if brief exists
        brief = brief_manager.get_brief(brief_id)
        if not brief:
            return jsonify({"ok": False, "error": "Brief not found"}), 404
        
        # Check if generator is available
        if not blueprint_generator.is_available():
            return jsonify({
                "ok": False,
                "error": "Blueprint generator not available - OpenAI API key not configured"
            }), 503
        
        # Create a new job
        job = brief_manager.create_job(brief_id)
        if not job:
            return jsonify({"ok": False, "error": "Failed to create job"}), 500
        
        # Start the job
        if not job_runner.start_job(job.id):
            return jsonify({"ok": False, "error": "Failed to start job"}), 500
        
        return jsonify({
            "ok": True,
            "job": {
                "id": job.id,
                "brief_id": job.brief_id,
                "status": job.status.value,
                "created_at": job.created_at
            }
        }), 202  # Accepted
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/jobs/<job_id>")
def get_job(job_id):
    """Get job status and results."""
    try:
        job = brief_manager.get_job(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job not found"}), 404
        
        job_data = {
            "id": job.id,
            "brief_id": job.brief_id,
            "status": job.status.value,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at
        }
        
        # Add result or error based on status
        if job.status.value == "completed" and job.result:
            job_data["result"] = job.result
        elif job.status.value == "failed":
            job_data["error"] = job.error
            if job.result:
                job_data["details"] = job.result
        
        return jsonify({
            "ok": True,
            "job": job_data
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/jobs")
def list_jobs():
    """List all jobs."""
    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        
        brief_id = request.args.get('brief_id')  # Optional filter
        
        jobs = brief_manager.list_jobs(brief_id=brief_id, limit=limit)
        
        jobs_data = []
        for job in jobs:
            job_data = {
                "id": job.id,
                "brief_id": job.brief_id,
                "status": job.status.value,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at
            }
            
            # Add summary result info
            if job.status.value == "completed" and job.result:
                job_data["has_result"] = True
            elif job.status.value == "failed":
                job_data["error"] = job.error
                job_data["has_result"] = False
            else:
                job_data["has_result"] = False
            
            jobs_data.append(job_data)
        
        return jsonify({
            "ok": True,
            "jobs": jobs_data,
            "count": len(jobs_data)
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

# Import the new modules
from app.export_pack import export_pack_generator
from app.gcs_storage import gcs_storage

@app.post("/jobs/<job_id>:export")
def export_job(job_id):
    """Export a completed job as a ZIP package."""
    try:
        # Get the job
        job = brief_manager.get_job(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job not found"}), 404
        
        # Check if job is completed
        if job.status.value != "completed":
            return jsonify({
                "ok": False, 
                "error": f"Job must be completed to export (current status: {job.status.value})"
            }), 400
        
        # Get the brief
        brief = brief_manager.get_brief(job.brief_id)
        if not brief:
            return jsonify({"ok": False, "error": "Brief not found"}), 404
        
        # Get the blueprint from job result
        if not job.result or "blueprint" not in job.result:
            return jsonify({"ok": False, "error": "No blueprint found in job result"}), 400
        
        blueprint = job.result["blueprint"]
        
        # Generate export pack
        success, result = export_pack_generator.generate_export_pack(
            blueprint, brief.content, job_id
        )
        
        if not success:
            return jsonify({"ok": False, "error": result}), 500
        
        zip_file_path = result
        
        # Upload to GCS and get signed URL
        remote_filename = f"exports/{job_id}/{os.path.basename(zip_file_path)}"
        upload_success, signed_url_or_error = gcs_storage.upload_file(zip_file_path, remote_filename)
        
        if not upload_success:
            # If GCS upload fails, still return local file info
            return jsonify({
                "ok": True,
                "export": {
                    "job_id": job_id,
                    "local_file": zip_file_path,
                    "download_url": f"/download/{os.path.basename(zip_file_path)}",
                    "gcs_error": signed_url_or_error,
                    "generated_at": time.time()
                }
            })
        
        return jsonify({
            "ok": True,
            "export": {
                "job_id": job_id,
                "download_url": signed_url_or_error,
                "local_file": zip_file_path,
                "generated_at": time.time()
            }
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/download/<filename>")
def download_file(filename):
    """Download a local export file."""
    try:
        file_path = Path("data/exports") / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        from flask import send_file
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
