"""
Standardized error handling for OttoMate API.
Provides consistent error response formats.
"""

from flask import jsonify
from typing import Dict, Any, Tuple

def api_error(message: str, status_code: int = 400, details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized API error response.

    Args:
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details (optional)

    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        "ok": False,
        "error": message
    }

    if details:
        response["details"] = details

    return jsonify(response), status_code

def validation_error(message: str, violations: list = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a validation error response.

    Args:
        message: Error message
        violations: List of validation violations

    Returns:
        Tuple of (response_dict, 422)
    """
    details = {}
    if violations:
        details["violations"] = violations

    return api_error(message, 422, details)

def not_found_error(resource: str, resource_id: str = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a not found error response.

    Args:
        resource: Type of resource (e.g., "Brief", "Job")
        resource_id: ID of the resource (optional)

    Returns:
        Tuple of (response_dict, 404)
    """
    if resource_id:
        message = f"{resource} '{resource_id}' not found"
    else:
        message = f"{resource} not found"

    return api_error(message, 404)

def server_error(message: str = None, exception: Exception = None) -> Tuple[Dict[str, Any], int]:
    """
    Create a server error response.

    Args:
        message: Custom error message (optional)
        exception: Exception object (optional)

    Returns:
        Tuple of (response_dict, 500)
    """
    if message:
        error_message = message
    elif exception:
        error_message = f"Internal server error: {str(exception)}"
    else:
        error_message = "Internal server error"

    return api_error(error_message, 500)

def bad_request_error(message: str) -> Tuple[Dict[str, Any], int]:
    """
    Create a bad request error response.

    Args:
        message: Error message

    Returns:
        Tuple of (response_dict, 400)
    """
    return api_error(message, 400)