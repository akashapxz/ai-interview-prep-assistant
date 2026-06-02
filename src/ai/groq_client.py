"""
Groq AI Client — Alternative LLM using Groq + Llama models.
Drop-in replacement for Gemini with same interface.
"""

import os
import json
import logging
import streamlit as st
from typing import Optional, Dict, Any
from groq import Groq
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_CODE_MODEL = "llama-3.1-70b-versatile"


@st.cache_resource
def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in .env")
    return Groq(api_key=api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8), reraise=True)
def groq_generate_text(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def groq_generate_json(prompt: str, temperature: float = 0.3) -> Optional[Dict[str, Any]]:
    try:
        raw = groq_generate_text(prompt + "\n\nRespond ONLY with valid JSON.", temperature=temperature)
        
        # Robust JSON extraction
        raw = raw.strip()
        first_brace = raw.find('{')
        first_bracket = raw.find('[')
        if first_brace == -1:
            start_idx = first_bracket
        elif first_bracket == -1:
            start_idx = first_brace
        else:
            start_idx = min(first_brace, first_bracket)

        last_brace = raw.rfind('}')
        last_bracket = raw.rfind(']')
        if last_brace == -1:
            end_idx = last_bracket
        elif last_bracket == -1:
            end_idx = last_brace
        else:
            end_idx = max(last_brace, last_bracket)

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            raw = raw[start_idx:end_idx+1]
            
        return json.loads(raw, strict=False)
    except Exception as e:
        logger.error(f"groq_generate_json error: {e}")
        return None


# ─────────────────────────────────────────────
# Unified LLM client — selects provider based on setting
# ─────────────────────────────────────────────

def get_ai_provider() -> str:
    """Returns the currently selected AI provider from session state."""
    return st.session_state.get("ai_provider", "gemini")


def generate_text(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    provider = get_ai_provider()
    if provider == "groq":
        return groq_generate_text(prompt, temperature, max_tokens)
    from src.ai.gemini_client import generate_text as gemini_gen
    return gemini_gen(prompt, temperature, max_tokens)


def generate_json(prompt: str, temperature: float = 0.3) -> Optional[Dict]:
    provider = get_ai_provider()
    if provider == "groq":
        return groq_generate_json(prompt, temperature)
    from src.ai.gemini_client import generate_json as gemini_json
    return gemini_json(prompt, temperature)
