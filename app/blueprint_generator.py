"""
Blueprint Generator using OpenAI GPT for OttoMate API.
"""

import json
import logging
import os
from typing import Dict, Any, Tuple, Optional
from app.lint_runner import lint
from app.config import get_openai_api_key, MOCK_BLUEPRINT_VERSION, MOCK_GMAIL_APP, MOCK_SLACK_APP, MOCK_SLACK_CHANNEL

logger = logging.getLogger(__name__)

class BlueprintGenerator:
    """Generates Make.com blueprints from natural language briefs using OpenAI."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client if API key is available."""
        try:
            api_key = get_openai_api_key()
            if api_key:
                # For now, we'll just store the key - actual OpenAI integration would go here
                self.api_key = api_key
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found in environment")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def is_available(self) -> bool:
        """Check if the blueprint generator is available."""
        return hasattr(self, 'api_key') and self.api_key is not None
    
    def generate_blueprint(self, brief: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a Make.com blueprint from a natural language brief.
        
        Returns:
            Tuple of (success: bool, result: dict)
        """
        if not self.is_available():
            return False, {
                "error": "OpenAI API key not configured",
                "violations": []
            }
        
        try:
            # For demo purposes, return a mock blueprint
            # In production, this would call OpenAI API
            mock_blueprint = {
                "version": MOCK_BLUEPRINT_VERSION,
                "triggerId": "gmail-trigger",
                "modules": [
                    {
                        "id": "gmail-trigger",
                        "type": "trigger",
                        "name": "Gmail New Email",
                        "params": {
                            "app": MOCK_GMAIL_APP,
                            "trigger_type": "new_email",
                            "filter": brief
                        }
                    },
                    {
                        "id": "slack-action",
                        "type": "action",
                        "name": "Send Slack Message",
                        "params": {
                            "app": MOCK_SLACK_APP,
                            "action_type": "send_message",
                            "channel": MOCK_SLACK_CHANNEL,
                            "message": f"New email: {brief}"
                        }
                    }
                ],
                "connections": [
                    {
                        "from": "gmail-trigger",
                        "to": "slack-action"
                    }
                ]
            }
            
            # Validate the generated blueprint
            lint_result = lint(mock_blueprint)
            
            if lint_result["ok"]:
                return True, {
                    "blueprint": mock_blueprint,
                    "generated_at": "mock_generation"
                }
            else:
                return False, {
                    "error": "Generated blueprint failed validation",
                    "violations": lint_result["violations"]
                }
                
        except Exception as e:
            logger.error(f"Blueprint generation failed: {e}")
            return False, {
                "error": f"Generation failed: {str(e)}",
                "violations": []
            }

# Global instance
blueprint_generator = BlueprintGenerator()
