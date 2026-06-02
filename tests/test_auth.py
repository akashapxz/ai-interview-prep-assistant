"""
Unit Tests for Authentication System
"""

import pytest
from unittest.mock import MagicMock, patch
from src.auth.supabase_auth import sign_up, sign_in, restore_session_from_token

@pytest.fixture
def mock_supabase():
    with patch("src.auth.supabase_auth.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client

def test_sign_in_success(mock_supabase):
    mock_res = MagicMock()
    mock_res.user = MagicMock(id="test-uid", email="test@test.com")
    mock_res.session = MagicMock(access_token="acc", refresh_token="ref")
    mock_supabase.auth.sign_in_with_password.return_value = mock_res
    
    with patch("src.auth.supabase_auth.get_profile") as mock_prof:
        mock_prof.return_value = {"full_name": "Test User"}
        with patch("streamlit.session_state", {}) as mock_ss:
            success, msg = sign_in("test@test.com", "password")
            assert success is True
            assert "successful" in msg.lower()

def test_sign_in_failure(mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
    
    success, msg = sign_in("test@test.com", "password")
    assert success is False
    assert "invalid" in msg.lower() or "credentials" in msg.lower()
