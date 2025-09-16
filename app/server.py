import os
import time
from pathlib import Path
import json
from flask import Flask, request, jsonify
from app.config import MIN_LIMIT, MAX_LIMIT, DEFAULT_LIMIT, DEFAULT_HOST, get_port
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
        limit = request.args.get('limit', DEFAULT_LIMIT, type=int)
        limit = min(max(MIN_LIMIT, limit), MAX_LIMIT)  # Clamp between min and max
        
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
        limit = request.args.get('limit', DEFAULT_LIMIT, type=int)
        limit = min(max(MIN_LIMIT, limit), MAX_LIMIT)  # Clamp between min and max
        
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
    app.run(host=DEFAULT_HOST, port=get_port())

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

# Import test harness and blueprint diff
from app.test_harness import test_harness
from app.blueprint_diff import blueprint_diff

@app.post("/test/payloads")
def create_test_payload():
    """Create a new test payload."""
    try:
        data = request.get_json(force=True, silent=False)
        
        name = data.get("name")
        description = data.get("description", "")
        payload_data = data.get("data", {})
        expected_output = data.get("expected_output")
        
        if not name or not payload_data:
            return jsonify({"ok": False, "error": "Name and data are required"}), 400
        
        payload_id = test_harness.add_payload(name, description, payload_data, expected_output)
        
        return jsonify({
            "ok": True,
            "payload": {
                "id": payload_id,
                "name": name,
                "description": description
            }
        }), 201
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/test/payloads")
def list_test_payloads():
    """List all test payloads."""
    try:
        payloads = test_harness.list_payloads()
        
        payload_data = []
        for payload in payloads:
            payload_data.append({
                "id": payload.id,
                "name": payload.name,
                "description": payload.description,
                "created_at": payload.created_at
            })
        
        return jsonify({
            "ok": True,
            "payloads": payload_data,
            "count": len(payload_data)
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/test/payloads/<payload_id>:run")
def run_test(payload_id):
    """Run a test with the specified payload."""
    try:
        data = request.get_json() or {}
        webhook_url = data.get("webhook_url")
        
        result_id = test_harness.run_test(payload_id, webhook_url)
        result = test_harness.get_result(result_id)
        
        if not result:
            return jsonify({"ok": False, "error": "Test execution failed"}), 500
        
        return jsonify({
            "ok": True,
            "test_result": {
                "id": result.id,
                "payload_id": result.payload_id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "webhook_url": result.webhook_url,
                "created_at": result.created_at
            }
        }), 201
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/test/results/<result_id>")
def get_test_result(result_id):
    """Get a specific test result."""
    try:
        result = test_harness.get_result(result_id)
        
        if not result:
            return jsonify({"ok": False, "error": "Test result not found"}), 404
        
        return jsonify({
            "ok": True,
            "result": {
                "id": result.id,
                "payload_id": result.payload_id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "response_data": result.response_data,
                "error_message": result.error_message,
                "webhook_url": result.webhook_url,
                "created_at": result.created_at
            }
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/test/results")
def list_test_results():
    """List all test results."""
    try:
        payload_id = request.args.get("payload_id")
        results = test_harness.list_results(payload_id)
        
        result_data = []
        for result in results:
            result_data.append({
                "id": result.id,
                "payload_id": result.payload_id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "webhook_url": result.webhook_url,
                "created_at": result.created_at,
                "has_error": result.error_message is not None
            })
        
        return jsonify({
            "ok": True,
            "results": result_data,
            "count": len(result_data)
        })
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/test/summary")
def get_test_summary():
    """Get test execution summary."""
    try:
        payload_id = request.args.get("payload_id")
        summary = test_harness.get_test_summary(payload_id)
        
        return jsonify({
            "ok": True,
            "summary": summary
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/blueprints/diff")
def diff_blueprints():
    """Compare two blueprints and return differences."""
    try:
        data = request.get_json(force=True, silent=False)

        blueprint1 = data.get("blueprint1")
        blueprint2 = data.get("blueprint2")
        output_format = data.get("format", "json")  # "json" or "text"

        if not blueprint1 or not blueprint2:
            return jsonify({"ok": False, "error": "Both blueprint1 and blueprint2 are required"}), 400

        # Perform the diff
        diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

        if output_format == "text":
            # Return human-readable text format
            diff_text = blueprint_diff.format_diff_human_readable(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_text,
                "format": "text",
                "summary": diff_result.summary,
                "is_identical": diff_result.is_identical
            })
        else:
            # Return structured JSON format
            diff_json = blueprint_diff.format_diff_json(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_json,
                "format": "json"
            })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/jobs/<job_id>/diff")
def diff_job_blueprint():
    """Compare a job's blueprint with another blueprint."""
    try:
        data = request.get_json(force=True, silent=False)
        other_blueprint = data.get("blueprint")
        output_format = data.get("format", "json")

        if not other_blueprint:
            return jsonify({"ok": False, "error": "Blueprint to compare is required"}), 400

        # Get the job
        job = brief_manager.get_job(job_id)
        if not job:
            return jsonify({"ok": False, "error": "Job not found"}), 404

        # Check if job has a blueprint result
        if not job.result or "blueprint" not in job.result:
            return jsonify({"ok": False, "error": "Job has no blueprint to compare"}), 400

        job_blueprint = job.result["blueprint"]

        # Perform the diff
        diff_result = blueprint_diff.compare_blueprints(job_blueprint, other_blueprint)

        if output_format == "text":
            diff_text = blueprint_diff.format_diff_human_readable(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_text,
                "format": "text",
                "summary": diff_result.summary,
                "is_identical": diff_result.is_identical,
                "job_id": job_id
            })
        else:
            diff_json = blueprint_diff.format_diff_json(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_json,
                "format": "json",
                "job_id": job_id
            })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/jobs/<job_id>/compare/<other_job_id>")
def compare_job_blueprints(job_id, other_job_id):
    """Compare blueprints from two different jobs."""
    try:
        output_format = request.args.get("format", "json")

        # Get both jobs
        job1 = brief_manager.get_job(job_id)
        job2 = brief_manager.get_job(other_job_id)

        if not job1:
            return jsonify({"ok": False, "error": f"Job {job_id} not found"}), 404
        if not job2:
            return jsonify({"ok": False, "error": f"Job {other_job_id} not found"}), 404

        # Check if both jobs have blueprint results
        if not job1.result or "blueprint" not in job1.result:
            return jsonify({"ok": False, "error": f"Job {job_id} has no blueprint to compare"}), 400
        if not job2.result or "blueprint" not in job2.result:
            return jsonify({"ok": False, "error": f"Job {other_job_id} has no blueprint to compare"}), 400

        blueprint1 = job1.result["blueprint"]
        blueprint2 = job2.result["blueprint"]

        # Perform the diff
        diff_result = blueprint_diff.compare_blueprints(blueprint1, blueprint2)

        if output_format == "text":
            diff_text = blueprint_diff.format_diff_human_readable(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_text,
                "format": "text",
                "summary": diff_result.summary,
                "is_identical": diff_result.is_identical,
                "job1_id": job_id,
                "job2_id": other_job_id
            })
        else:
            diff_json = blueprint_diff.format_diff_json(diff_result)
            return jsonify({
                "ok": True,
                "diff": diff_json,
                "format": "json",
                "job1_id": job_id,
                "job2_id": other_job_id
            })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
