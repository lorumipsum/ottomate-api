"""
Blueprint Generator using OpenAI GPT for OttoMate API.
"""

import json
import logging
import os
from typing import Dict, Any, Tuple, Optional
from app.lint_runner import lint
from app.config import get_openai_api_key, MOCK_BLUEPRINT_VERSION, MOCK_GMAIL_APP, MOCK_SLACK_APP, MOCK_SLACK_CHANNEL

try:
    import openai
except ImportError:
    openai = None

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
            if api_key and openai:
                # Initialize OpenAI client (v1.x.x format)
                self.client = openai.OpenAI(api_key=api_key)
                self.api_key = api_key
                logger.info("OpenAI client initialized successfully")
            elif not openai:
                logger.warning("OpenAI library not installed - using mock generation")
                self.client = None
            else:
                logger.warning("OpenAI API key not found in environment - using mock generation")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if the blueprint generator is available."""
        # Available if we have OpenAI client OR fallback to mock
        return self.client is not None or True  # Always available (fallback to mock)
    
    def generate_blueprint(self, brief: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a Make.com blueprint from a natural language brief.

        Returns:
            Tuple of (success: bool, result: dict)
        """
        try:
            if self.client and openai:
                # Use real OpenAI API
                return self._generate_with_openai(brief)
            else:
                # Fallback to mock generation
                logger.info("Using mock blueprint generation (OpenAI not available)")
                return self._generate_mock_blueprint(brief)

        except Exception as e:
            logger.error(f"Blueprint generation failed: {e}")
            return False, {
                "error": f"Generation failed: {str(e)}",
                "violations": []
            }

    def _generate_with_openai(self, brief: str) -> Tuple[bool, Dict[str, Any]]:
        """Generate blueprint using OpenAI API."""
        try:
            # Load blueprint schema for context
            schema_context = self._get_schema_context()

            # Create the prompt for OpenAI
            prompt = self._create_blueprint_prompt(brief, schema_context)

            # Call OpenAI API (v1.x.x format)
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Make.com automation expert. Generate valid Make.com blueprints from natural language descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # Extract the blueprint JSON from response
            blueprint_text = response.choices[0].message.content.strip()

            # Parse JSON from response (may be wrapped in markdown)
            blueprint = self._extract_json_from_response(blueprint_text)

            # Validate the generated blueprint
            lint_result = lint(blueprint)

            # Auto-repair once if validation fails
            if not lint_result["ok"]:
                logger.info(f"Blueprint validation failed, attempting auto-repair. Violations: {len(lint_result['violations'])}")
                repaired_blueprint = self._attempt_auto_repair(blueprint, lint_result["violations"])

                if repaired_blueprint:
                    repair_lint_result = lint(repaired_blueprint)
                    if repair_lint_result["ok"]:
                        logger.info("Auto-repair successful")
                        blueprint = repaired_blueprint
                        lint_result = repair_lint_result

            if lint_result["ok"]:
                return True, {
                    "blueprint": blueprint,
                    "generated_at": response.created,
                    "model": response.model,
                    "usage": response.usage._asdict() if hasattr(response.usage, '_asdict') else str(response.usage)
                }
            else:
                return False, {
                    "error": "Generated blueprint failed validation after auto-repair",
                    "violations": lint_result["violations"],
                    "raw_blueprint": blueprint
                }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return False, {
                "error": "OpenAI response was not valid JSON",
                "violations": []
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return False, {
                "error": f"OpenAI API error: {str(e)}",
                "violations": []
            }

    def _generate_mock_blueprint(self, brief: str) -> Tuple[bool, Dict[str, Any]]:
        """Generate mock blueprint for testing/demo purposes."""
        # Generate different mock blueprints based on brief content
        if "hubspot" in brief.lower() and "sheets" in brief.lower():
            # GB-1: HubSpot → Sheets + Slack
            mock_blueprint = {
                "version": MOCK_BLUEPRINT_VERSION,
                "triggerId": "hubspot-trigger",
                "modules": [
                    {
                        "id": "hubspot-trigger",
                        "type": "trigger",
                        "name": "HubSpot New Contact",
                        "params": {
                            "app": "HubSpot",
                            "trigger_type": "new_contact"
                        }
                    },
                    {
                        "id": "sheets-action",
                        "type": "action",
                        "name": "Google Sheets Append Row",
                        "params": {
                            "app": "Google Sheets",
                            "action_type": "append_row",
                            "spreadsheet_id": "{{hubspot-trigger.spreadsheet_url}}",
                            "range": "A:C",
                            "values": ["{{hubspot-trigger.email}}", "{{hubspot-trigger.first_name}}", "{{hubspot-trigger.last_name}}"]
                        }
                    },
                    {
                        "id": "slack-action",
                        "type": "action",
                        "name": "Send Slack Message",
                        "params": {
                            "app": "Slack",
                            "action_type": "send_message",
                            "channel": "#sales-alerts",
                            "message": "New HubSpot contact: {{hubspot-trigger.first_name}} {{hubspot-trigger.last_name}} ({{hubspot-trigger.email}})"
                        }
                    }
                ],
                "connections": [
                    {
                        "from": "hubspot-trigger",
                        "to": "sheets-action"
                    },
                    {
                        "from": "sheets-action",
                        "to": "slack-action"
                    }
                ]
            }
        elif "typeform" in brief.lower() and "airtable" in brief.lower():
            # GB-2: Typeform → Airtable + Gmail
            mock_blueprint = {
                "version": MOCK_BLUEPRINT_VERSION,
                "triggerId": "typeform-trigger",
                "modules": [
                    {
                        "id": "typeform-trigger",
                        "type": "trigger",
                        "name": "Typeform New Entry",
                        "params": {
                            "app": "Typeform",
                            "trigger_type": "new_entry",
                            "form_id": "{{form_id}}"
                        }
                    },
                    {
                        "id": "airtable-action",
                        "type": "action",
                        "name": "Airtable Create Record",
                        "params": {
                            "app": "Airtable",
                            "action_type": "create_record",
                            "base_id": "{{base_id}}",
                            "table_name": "Leads",
                            "fields": {
                                "Name": "{{typeform-trigger.name}}",
                                "Email": "{{typeform-trigger.email}}",
                                "Interest": "{{typeform-trigger.interest}}"
                            }
                        }
                    },
                    {
                        "id": "gmail-action",
                        "type": "action",
                        "name": "Gmail Create Draft",
                        "params": {
                            "app": "Gmail",
                            "action_type": "create_draft",
                            "to": "{{typeform-trigger.email}}",
                            "subject": "Thank you for your interest, {{typeform-trigger.name}}",
                            "body": "Hi {{typeform-trigger.name}},\n\nThank you for your interest in {{typeform-trigger.interest}}. We'll be in touch soon!\n\nBest regards,\nThe Team"
                        }
                    }
                ],
                "connections": [
                    {
                        "from": "typeform-trigger",
                        "to": "airtable-action"
                    },
                    {
                        "from": "airtable-action",
                        "to": "gmail-action"
                    }
                ]
            }
        else:
            # Default mock blueprint
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

        # Validate the mock blueprint
        lint_result = lint(mock_blueprint)

        if lint_result["ok"]:
            return True, {
                "blueprint": mock_blueprint,
                "generated_at": "mock_generation"
            }
        else:
            return False, {
                "error": "Mock blueprint failed validation",
                "violations": lint_result["violations"]
            }

    def _get_schema_context(self) -> str:
        """Get blueprint schema context for OpenAI prompt."""
        try:
            # Read the blueprint schema
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema', 'blueprint.schema.json')
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            return json.dumps(schema, indent=2)
        except Exception:
            return "Schema not available"

    def _create_blueprint_prompt(self, brief: str, schema_context: str) -> str:
        """Create the prompt for OpenAI blueprint generation."""
        return f"""
Generate a valid Make.com blueprint JSON that implements this automation requirement:

BRIEF: {brief}

The blueprint must follow this exact JSON schema:
{schema_context}

Requirements:
1. Generate a complete, valid blueprint that follows the schema exactly
2. Include realistic module IDs, names, and parameters
3. Ensure all modules are connected properly (no orphaned modules)
4. Use appropriate app names (Gmail, Slack, HubSpot, Google Sheets, Airtable, etc.)
5. Include required parameters for each module type
6. Make sure the triggerId matches one of the module IDs
7. The version should be "v1.0"

Return ONLY the JSON blueprint, no explanation or markdown formatting.
"""

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from OpenAI response, handling markdown formatting."""
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()

        # Parse JSON
        return json.loads(response_text.strip())

    def _attempt_auto_repair(self, blueprint: Dict[str, Any], violations: list) -> Optional[Dict[str, Any]]:
        """Attempt to auto-repair common blueprint issues."""
        repaired = blueprint.copy()

        try:
            # Fix common issues

            # Ensure version is set
            if "version" not in repaired or not repaired["version"]:
                repaired["version"] = "v1.0"

            # Ensure triggerId matches a module
            if "modules" in repaired and repaired["modules"]:
                module_ids = [mod.get("id") for mod in repaired["modules"] if mod.get("id")]
                if repaired.get("triggerId") not in module_ids:
                    # Set triggerId to first trigger-type module or first module
                    trigger_modules = [mod for mod in repaired["modules"] if mod.get("type") == "trigger"]
                    if trigger_modules:
                        repaired["triggerId"] = trigger_modules[0]["id"]
                    elif module_ids:
                        repaired["triggerId"] = module_ids[0]

            # Ensure connections array exists
            if "connections" not in repaired:
                repaired["connections"] = []

            # Ensure modules array exists
            if "modules" not in repaired:
                repaired["modules"] = []

            return repaired

        except Exception as e:
            logger.error(f"Auto-repair failed: {e}")
            return None

# Global instance
blueprint_generator = BlueprintGenerator()
