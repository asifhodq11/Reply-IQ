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

from unittest.mock import patch, MagicMock
from app.services.ai_engine import generate_reply

@patch('app.services.ai_engine.call_llm')
def test_generate_reply_pipeline_standard(mock_call_llm):
    """
    Verifies that all 3 passes are called exactly once in sequence
    and the final output is returned.
    """
    # Mock returns for each pass
    mock_call_llm.side_effect = [
        "Pass 1: Professional reply.",
        "Pass 2: Humanised reply.",
        "Pass 3: Final audited reply."
    ]
    
    result = generate_reply(
        business_name="Test Cafe",
        business_type="Cafe",
        tone_preference="friendly",
        star_rating=4,
        review_text="Good food but slow."
    )
    
    # 1. Verify 3 calls
    assert mock_call_llm.call_count == 3
    
    # 2. Verify model choice for 'standard' complexity
    # rating 4 + text -> standard -> openai/gpt-4o-mini (openrouter mode)
    for call in mock_call_llm.call_args_list:
        assert call[0][2] == 'openai/gpt-4o-mini'
    
    # 3. Verify final return
    assert result == "Pass 3: Final audited reply."

@patch('app.services.ai_engine.call_llm')
def test_generate_reply_model_routing_crisis(mock_call_llm):
    """Verifies that crisis reviews route to GPT-4o full."""
    mock_call_llm.return_value = "Crisis reply."
    
    generate_reply(
        business_name="Test Cafe",
        business_type="Cafe",
        tone_preference="friendly",
        star_rating=1,
        review_text="I am going to sue you for food poisoning."
    )
    
    # Verify first call used the crisis model (openrouter mode)
    model_used = mock_call_llm.call_args_list[0][0][2]
    assert model_used == 'openai/gpt-4o'


@patch('app.services.ai_engine.call_llm')
def test_generate_reply_model_routing_simple(mock_call_llm):
    """Verifies that simple reviews route to Gemini Flash-Lite."""
    mock_call_llm.return_value = "Simple reply."
    
    generate_reply(
        business_name="Test Cafe",
        business_type="Cafe",
        tone_preference="friendly",
        star_rating=5,
        review_text="Great!"
    )
    
    # Verify model choice (openrouter mode)
    model_used = mock_call_llm.call_args_list[0][0][2]
    assert model_used == 'google/gemini-2.0-flash-lite'


@patch('app.services.ai_engine.call_llm')
def test_prompt_content_pass_2_patterns(mock_call_llm):
    """Verifies that the 24 patterns are actually passed in the Pass 2 prompt."""
    mock_call_llm.return_value = "Stub."
    
    generate_reply(
        business_name="X",
        business_type="Y",
        tone_preference="Z",
        star_rating=5,
        review_text="OK"
    )
    
    # Call 0 = Pass 1
    # Call 1 = Pass 2
    user_prompt_pass_2 = mock_call_llm.call_args_list[1][0][1]
    
    assert "PATTERNS TO STRIP:" in user_prompt_pass_2
    assert "Em dashes" in user_prompt_pass_2
    assert "24. Over-specified conclusions" in user_prompt_pass_2
