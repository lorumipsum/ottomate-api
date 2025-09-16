"""
Configuration constants for OttoMate API.
Centralizes hardcoded values for better maintainability.
"""

import os

# Server Configuration
DEFAULT_PORT = 8080
DEFAULT_HOST = "0.0.0.0"

# Pagination Limits
MIN_LIMIT = 1
MAX_LIMIT = 100
DEFAULT_LIMIT = 50

# Logging Configuration
LOG_TRUNCATE_LENGTH = 2000

# Webhook Configuration
WEBHOOK_TIMEOUT_SECONDS = 10

# Mock Blueprint Configuration
MOCK_BLUEPRINT_VERSION = "v1.0"
MOCK_GMAIL_APP = "Gmail"
MOCK_SLACK_APP = "Slack"
MOCK_SLACK_CHANNEL = "#alerts"

# Environment Variables
def get_port() -> int:
    """Get port from environment or use default."""
    return int(os.environ.get("PORT", DEFAULT_PORT))

def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    return os.getenv('OPENAI_API_KEY', '')

def get_lim_api_key() -> str:
    """Get LIM API key from environment."""
    return os.getenv('LIM_API_KEY', '')