import os

# Set dummy env vars BEFORE any app imports
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
FAKE_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.fake'
os.environ['SUPABASE_ANON_KEY'] = FAKE_JWT
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = FAKE_JWT
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['GEMINI_API_KEY'] = 'test-gemini-key'
os.environ['OPENROUTER_API_KEY'] = 'test-openrouter-key'
os.environ['AI_PROVIDER'] = 'openrouter'
os.environ['FRONTEND_URL'] = 'http://localhost'

import pytest
from app.services.model_router import classify_complexity, get_model_for_complexity

def test_classify_crisis():
    # Crisis: rating <= 2 AND contains crisis word
    assert classify_complexity(1, "I'm going to call my lawyer.") == 'crisis'
    assert classify_complexity(2, "The food poisoning was terrible.") == 'crisis'
    # Mixed: crisis word but high rating -> Simple (because rating > 2 and count < 30)
    assert classify_complexity(5, "The sick beat at the restaurant was sick!") == 'simple'
    # No word but low rating -> Not crisis
    assert classify_complexity(1, "I hated it.") == 'standard'

def test_classify_simple():
    # Simple: rating == 5 AND word count < 30 AND no crisis word
    assert classify_complexity(5, "Great food!") == 'simple'
    # Exactly 29 words
    short_text = " ".join(["word"] * 29)
    assert classify_complexity(5, short_text) == 'simple'
    # Exactly 30 words -> Standard
    long_text = " ".join(["word"] * 30)
    assert classify_complexity(5, long_text) == 'standard'

def test_classify_standard():
    # Everything else
    assert classify_complexity(4, "Good service.") == 'standard'
    assert classify_complexity(3, "Average.") == 'standard'
    assert classify_complexity(2, "Poor.") == 'standard' # No crisis word

def test_model_mapping():
    # Default provider is openrouter — expect prefixed names
    assert get_model_for_complexity('crisis') == 'openai/gpt-4o'
    assert get_model_for_complexity('simple') == 'google/gemini-2.0-flash-lite'
    assert get_model_for_complexity('standard') == 'openai/gpt-4o-mini'
    assert get_model_for_complexity('unknown') == 'openai/gpt-4o-mini'
