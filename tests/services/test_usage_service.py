import os

# Set dummy env vars BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
FAKE_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake'
os.environ['SUPABASE_ANON_KEY'] = FAKE_JWT
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = FAKE_JWT
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['FRONTEND_URL'] = 'http://localhost'

import pytest
from unittest.mock import patch, MagicMock
from app.services.usage_service import check_usage_limit, increment_usage, get_plan_limit
from app.utils.exceptions import ReplyLimitReached


def test_plan_limits():
    assert get_plan_limit('free') == 5
    assert get_plan_limit('starter') == 50
    assert get_plan_limit('growth') == 999999
    assert get_plan_limit('pro') == 999999
    assert get_plan_limit('other') == 5  # Default to free


def _mock_supabase_user(plan, count, billing_start='2026-03-01'):
    """Helper: returns a mock supabase client whose .from_().select()...single().execute()
    returns the given user data."""
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = {
        'plan': plan,
        'reply_count_this_month': count,
        'billing_cycle_start': billing_start,
    }
    # Chain: .from_().select().eq().single().execute()
    (mock_supabase
        .from_.return_value
        .select.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value) = mock_result
    return mock_supabase


@patch('app.services.usage_service.supabase')
def test_check_usage_limit_under(mock_supabase):
    mock_supabase.from_ = _mock_supabase_user('free', 0).from_
    # Should not raise — user is under the limit
    check_usage_limit('test-user-uuid')


@patch('app.services.usage_service.supabase')
def test_check_usage_limit_at_boundary(mock_supabase):
    mock_supabase.from_ = _mock_supabase_user('free', 5).from_
    with pytest.raises(ReplyLimitReached) as excinfo:
        check_usage_limit('test-user-uuid')

    assert excinfo.value.error_code == 'REPLY_LIMIT_REACHED'
    assert excinfo.value.details['replies_used'] == 5


@patch('app.services.usage_service.supabase')
def test_check_usage_limit_over(mock_supabase):
    mock_supabase.from_ = _mock_supabase_user('starter', 51).from_
    with pytest.raises(ReplyLimitReached) as excinfo:
        check_usage_limit('test-user-uuid')

    assert excinfo.value.http_status == 403
    assert excinfo.value.details['replies_limit'] == 50


@patch('app.services.usage_service.supabase')
def test_increment_usage_atomic(mock_supabase):
    # Setup mock rpc call
    mock_rpc = MagicMock()
    mock_supabase.rpc.return_value = mock_rpc

    increment_usage("test-user-uuid")

    mock_supabase.rpc.assert_called_once_with(
        'increment_reply_count',
        {'user_id_input': "test-user-uuid"}
    )
    mock_rpc.execute.assert_called_once()
