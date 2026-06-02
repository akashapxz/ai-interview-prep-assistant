"""
Unit Tests for AI Models & Prompts
"""

import pytest
from unittest.mock import patch, MagicMock
import os
os.environ["GEMINI_API_KEY"] = "mock_gemini_api_key_value"

from src.ai.gemini_client import generate_text, generate_json

@patch("google.generativeai.GenerativeModel")
def test_generate_text(mock_model_class):
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    mock_response = MagicMock()
    mock_response.text = "Hello world"
    mock_model.generate_content.return_value = mock_response

    res = generate_text("Say hello")
    assert res == "Hello world"

@patch("src.ai.gemini_client.generate_text")
def test_generate_json(mock_gen_text):
    mock_gen_text.return_value = '{"status": "ok"}'
    res = generate_json("Get json status")
    assert res == {"status": "ok"}
