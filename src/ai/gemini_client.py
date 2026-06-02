"""
Gemini AI Client — Primary LLM integration using Google Gemini 2.5 Flash.
Supports text generation, structured JSON output, and streaming.
"""

import os
import json
import time
import logging
import streamlit as st
from typing import Optional, Dict, Any, Generator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"
MAX_TOKENS = 8192
TEMPERATURE = 0.7


@st.cache_resource
def _init_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.types.GenerationConfig(
            temperature=TEMPERATURE,
            max_output_tokens=MAX_TOKENS,
            top_p=0.95,
        ),
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    )


# ─────────────────────────────────────────────
# Multi-LLM Providers Support and Routing
# ─────────────────────────────────────────────

import requests

def _generate_text_gemini(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    model = _init_gemini()
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()

def _generate_text_groq(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    from src.ai.groq_client import groq_generate_text
    return groq_generate_text(prompt, temperature, max_tokens)

def _generate_text_openai(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in .env")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()

def _generate_text_anthropic(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured in .env")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": min(max_tokens, 4000),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30)
    res.raise_for_status()
    return res.json()["content"][0]["text"].strip()

def _generate_text_openrouter(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured in .env")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Interview Prep"
    }
    payload = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=30)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()


def _is_key_valid(key_name: str) -> bool:
    val = os.getenv(key_name, "")
    return bool(val and not val.startswith("your_") and val != "your_anthropic_api_key")


def generate_text(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """Generate text from selected LLM provider, with automatic fallback if quota/limit is exceeded."""
    primary = st.session_state.get("ai_provider", "gemini")
    
    # Standard failover chain order
    providers_order = ["gemini", "groq", "openai", "anthropic", "openrouter"]
    if primary in providers_order:
        providers_order.remove(primary)
        providers_order.insert(0, primary)
        
    errors = []
    for provider in providers_order:
        # Check API key configuration first to skip unconfigured options
        if provider == "gemini" and not _is_key_valid("GEMINI_API_KEY"):
            continue
        if provider == "groq" and not _is_key_valid("GROQ_API_KEY"):
            continue
        if provider == "openai" and not _is_key_valid("OPENAI_API_KEY"):
            continue
        if provider == "anthropic" and not _is_key_valid("ANTHROPIC_API_KEY"):
            continue
        if provider == "openrouter" and not _is_key_valid("OPENROUTER_API_KEY"):
            continue
            
        try:
            if provider == "gemini":
                return _generate_text_gemini(prompt, temperature, max_tokens)
            elif provider == "groq":
                return _generate_text_groq(prompt, temperature, max_tokens)
            elif provider == "openai":
                return _generate_text_openai(prompt, temperature, max_tokens)
            elif provider == "anthropic":
                return _generate_text_anthropic(prompt, temperature, max_tokens)
            elif provider == "openrouter":
                return _generate_text_openrouter(prompt, temperature, max_tokens)
        except Exception as e:
            err_msg = f"{provider} failed: {e}"
            logger.error(err_msg)
            errors.append(err_msg)
            # Add warning to sidebar notifying user of fallback
            try:
                st.sidebar.warning(f"⚠️ {provider.upper()} quota/error. Trying fallback...")
            except Exception:
                pass
                
    if errors:
        raise RuntimeError(f"All configured LLM providers failed. Errors: {'; '.join(errors)}")
    else:
        raise RuntimeError("No LLM providers are configured. Please check your environment variables.")


def generate_json(prompt: str, temperature: float = 0.3) -> Optional[Dict[str, Any]]:
    """Generate structured JSON. Routes & falls back via generate_text, then extracts and parses JSON response."""
    try:
        # Explicitly instruct the model to return only JSON
        json_prompt = prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown wrappers, no explanations, no text outside the JSON block."
        raw = generate_text(json_prompt, temperature=temperature, max_tokens=8192)
        
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
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {raw[:500] if 'raw' in locals() else 'None'}")
        return None
    except Exception as e:
        logger.error(f"generate_json error: {e}")
        return None


def stream_text(prompt: str) -> Generator[str, None, None]:
    """Stream text tokens from selected provider, with automatic fallback support."""
    primary = st.session_state.get("ai_provider", "gemini")
    
    providers_order = ["gemini", "groq", "openai", "anthropic", "openrouter"]
    if primary in providers_order:
        providers_order.remove(primary)
        providers_order.insert(0, primary)
        
    for provider in providers_order:
        # Check API key configuration first to skip unconfigured options
        if provider == "gemini" and not _is_key_valid("GEMINI_API_KEY"):
            continue
        if provider == "groq" and not _is_key_valid("GROQ_API_KEY"):
            continue
        if provider == "openai" and not _is_key_valid("OPENAI_API_KEY"):
            continue
        if provider == "anthropic" and not _is_key_valid("ANTHROPIC_API_KEY"):
            continue
        if provider == "openrouter" and not _is_key_valid("OPENROUTER_API_KEY"):
            continue
            
        try:
            if provider == "gemini":
                model = _init_gemini()
                for chunk in model.generate_content(prompt, stream=True):
                    if chunk.text:
                        yield chunk.text
                return
            elif provider == "groq":
                from src.ai.groq_client import _get_groq_client, GROQ_MODEL
                client = _get_groq_client()
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                )
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                return
            elif provider == "openai" or provider == "openrouter":
                api_key = os.getenv("OPENAI_API_KEY" if provider == "openai" else "OPENROUTER_API_KEY", "")
                url = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "gpt-4o-mini" if provider == "openai" else "meta-llama/llama-3.3-70b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                }
                response = requests.post(url, json=payload, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                content = chunk_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if content:
                                    yield content
                            except:
                                pass
                return
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY", "")
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                }
                response = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, stream=True, timeout=10)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:].strip()
                            try:
                                chunk_data = json.loads(data_str)
                                if chunk_data.get("type") == "content_block_delta":
                                    content = chunk_data.get("delta", {}).get("text", "")
                                    if content:
                                        yield content
                            except:
                                pass
                return
        except Exception as e:
            logger.error(f"stream_text failed for {provider}: {e}")
            try:
                st.sidebar.warning(f"⚠️ {provider.upper()} limit/error. Trying stream fallback...")
            except:
                pass
                
    yield "Error: All configured streaming providers failed."


def generate_with_context(
    system_prompt: str,
    user_message: str,
    history: Optional[list] = None,
    temperature: float = 0.7,
) -> str:
    """Multi-turn conversation with context history."""
    try:
        model = _init_gemini()
        chat = model.start_chat(history=history or [])
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        response = chat.send_message(
            full_prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"generate_with_context error: {e}")
        return f"I encountered an error. Please try again. ({e})"


# ─────────────────────────────────────────────
# Module-specific wrappers
# ─────────────────────────────────────────────

def analyze_resume(resume_text: str, target_role: str = "") -> Optional[Dict]:
    from src.ai.prompts import RESUME_ANALYSIS_PROMPT
    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:6000],
        target_role=target_role or "Software Engineer",
    )
    return generate_json(prompt, temperature=0.2)


def generate_technical_questions(
    domain: str,
    difficulty: str,
    question_type: str,
    skills: str = "",
    count: int = 5,
) -> Optional[Dict]:
    from src.ai.prompts import TECHNICAL_QUESTION_PROMPT
    prompt = TECHNICAL_QUESTION_PROMPT.format(
        domain=domain,
        difficulty=difficulty,
        question_type=question_type,
        skills=skills or "General",
        count=count,
    )
    return generate_json(prompt, temperature=0.8)


def evaluate_technical_answer(question: str, answer: str, domain: str, difficulty: str) -> Optional[Dict]:
    from src.ai.prompts import TECHNICAL_EVAL_PROMPT
    prompt = TECHNICAL_EVAL_PROMPT.format(
        question=question,
        answer=answer,
        domain=domain,
        difficulty=difficulty,
    )
    return generate_json(prompt, temperature=0.2)


def generate_hr_questions(
    name: str,
    college: str,
    branch: str,
    target_role: str = "Software Engineer",
    focus_areas: str = "General",
    count: int = 5,
) -> Optional[Dict]:
    from src.ai.prompts import HR_QUESTION_PROMPT
    prompt = HR_QUESTION_PROMPT.format(
        name=name, college=college, branch=branch,
        target_role=target_role, focus_areas=focus_areas, count=count,
    )
    return generate_json(prompt, temperature=0.8)


def evaluate_hr_answer(question: str, answer: str) -> Optional[Dict]:
    from src.ai.prompts import HR_EVAL_PROMPT
    prompt = HR_EVAL_PROMPT.format(question=question, answer=answer)
    return generate_json(prompt, temperature=0.2)


def generate_coding_problem(topic: str, difficulty: str, language: str = "python") -> Optional[Dict]:
    from src.ai.prompts import CODING_PROBLEM_PROMPT
    prompt = CODING_PROBLEM_PROMPT.format(topic=topic, difficulty=difficulty, language=language)
    return generate_json(prompt, temperature=0.6)


def evaluate_code(problem: str, code: str, language: str) -> Optional[Dict]:
    from src.ai.prompts import CODING_EVAL_PROMPT
    prompt = CODING_EVAL_PROMPT.format(problem=problem, code=code, language=language)
    return generate_json(prompt, temperature=0.1)


def generate_mock_question(
    persona: str,
    interview_type: str,
    company: str,
    candidate_name: str,
    domain: str,
    difficulty: str,
    current_q: int,
    total_q: int,
    context: str,
    persona_traits: str,
) -> Optional[Dict]:
    from src.ai.prompts import MOCK_INTERVIEW_SYSTEM_PROMPT
    prompt = MOCK_INTERVIEW_SYSTEM_PROMPT.format(
        persona=persona, interview_type=interview_type, company=company,
        candidate_name=candidate_name, domain=domain, difficulty=difficulty,
        current_q=current_q, total_q=total_q, context=context, persona_traits=persona_traits,
    )
    return generate_json(prompt, temperature=0.85)


def generate_mock_report(
    interview_type: str,
    candidate_name: str,
    duration: int,
    total_q: int,
    transcript: str,
) -> Optional[Dict]:
    from src.ai.prompts import MOCK_INTERVIEW_FINAL_REPORT
    prompt = MOCK_INTERVIEW_FINAL_REPORT.format(
        interview_type=interview_type, candidate_name=candidate_name,
        duration=duration, total_q=total_q, transcript=transcript[:5000],
    )
    return generate_json(prompt, temperature=0.2)


def generate_company_questions(
    company: str,
    categories: str,
    difficulty: str,
    role_type: str,
    count: int = 8,
) -> Optional[Dict]:
    from src.ai.prompts import COMPANY_INTERVIEW_PROMPT
    prompt = COMPANY_INTERVIEW_PROMPT.format(
        company=company, categories=categories, difficulty=difficulty,
        role_type=role_type, count=count,
    )
    return generate_json(prompt, temperature=0.7)


def analyze_voice_transcript(transcript: str, wpm: int, duration: int) -> Optional[Dict]:
    from src.ai.prompts import VOICE_ANALYSIS_PROMPT
    prompt = VOICE_ANALYSIS_PROMPT.format(transcript=transcript, wpm=wpm, duration=duration)
    return generate_json(prompt, temperature=0.2)


def generate_learning_roadmap(
    name: str, branch: str, weak_areas: str, strong_areas: str,
    tech_score: float, hr_score: float, companies: str,
    weeks: int, history_summary: str,
) -> Optional[Dict]:
    from src.ai.prompts import LEARNING_ROADMAP_PROMPT
    prompt = LEARNING_ROADMAP_PROMPT.format(
        name=name, branch=branch, weak_areas=weak_areas, strong_areas=strong_areas,
        tech_score=tech_score, hr_score=hr_score, companies=companies,
        weeks=weeks, history_summary=history_summary,
    )
    return generate_json(prompt, temperature=0.5)


def chat_career_coach(
    name: str, branch: str, college: str,
    target_role: str, performance: str,
    message: str, history: str,
) -> str:
    from src.ai.prompts import CAREER_COACH_PROMPT
    prompt = CAREER_COACH_PROMPT.format(
        name=name, branch=branch, college=college,
        target_role=target_role, performance=performance,
        message=message, history=history,
    )
    return generate_text(prompt, temperature=0.75)


def transcribe_audio(audio_bytes: bytes) -> Optional[str]:
    """Transcribe audio bytes using either Gemini upload or Groq Whisper, with automatic failover."""
    import tempfile
    import os

    if not audio_bytes or len(audio_bytes) < 100:
        return ""

    provider = st.session_state.get("ai_provider", "gemini")

    def _transcribe_groq():
        from src.ai.groq_client import _get_groq_client
        client = _get_groq_client()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        try:
            with open(temp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(os.path.basename(temp_path), audio_file),
                    model="whisper-large-v3",
                    response_format="json",
                )
                return transcription.text.strip()
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _transcribe_gemini():
        import google.generativeai as genai
        _ = _init_gemini()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        try:
            audio_file = genai.upload_file(path=temp_path)
            model = _init_gemini()
            response = model.generate_content([
                "Please transcribe this audio accurately. Output only the transcription, no additional text.",
                audio_file
            ])
            return response.text.strip()
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    if provider == "groq":
        try:
            res = _transcribe_groq()
            if res:
                return res
        except Exception as e:
            logger.error(f"Groq transcription failed, falling back to Gemini: {e}")
        try:
            return _transcribe_gemini()
        except Exception as e:
            logger.error(f"Gemini fallback transcription failed: {e}")
            return None
    else:
        try:
            res = _transcribe_gemini()
            if res:
                return res
        except Exception as e:
            logger.error(f"Gemini transcription failed, falling back to Groq: {e}")
        try:
            return _transcribe_groq()
        except Exception as e:
            logger.error(f"Groq fallback transcription failed: {e}")
            return None

