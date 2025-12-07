"""Utility functions."""
import tiktoken
import logging
from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def get_response_schema():
    """Get JSON schema for structured outputs."""
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "items": {"type": "integer"},
                "minItems": 17,
                "maxItems": 17,
                "description": "Array of exactly 17 scores for questions Q1-Q17"
            },
            "manipulation_check": {
                "type": "string",
                "enum": ["YES", "NO"],
                "description": "Does the resume mention any criminal record information?"
            },
            "thought_process": {
                "type": "string",
                "description": "Brief 2-3 sentence explanation of evaluation reasoning"
            }
        },
        "required": ["scores", "manipulation_check", "thought_process"],
        "additionalProperties": False
    }


def get_claude_response_schema():
    """Get JSON schema for Claude API (removes minItems/maxItems from arrays)."""
    return {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Array of exactly 17 scores for questions Q1-Q17"
            },
            "manipulation_check": {
                "type": "string",
                "enum": ["YES", "NO"],
                "description": "Does the resume mention any criminal record information?"
            },
            "thought_process": {
                "type": "string",
                "description": "Brief 2-3 sentence explanation of evaluation reasoning"
            }
        },
        "required": ["scores", "manipulation_check", "thought_process"],
        "additionalProperties": False
    }


def calculate_token_count(prompt: str, model: str = "gpt-4o") -> int:
    """Calculate token count for a prompt."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning(f"Encoding not found for model {model}, using cl100k_base")
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(prompt)
    return len(tokens)


def process_txt_files_and_attach_to_prompt(file_path: str, global_prompt_template: str) -> str:
    """Read resume text and construct prompt."""
    with open(file_path, 'r', encoding='utf-8') as file:
        extracted_text = file.read().strip()
    
    full_prompt = f"""RESUME:
{extracted_text}

---

EVALUATION QUESTIONS:
{global_prompt_template}"""
    
    return full_prompt

