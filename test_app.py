from unittest.mock import patch
from app import generate_summary


@patch("app.call_openrouter_api")
def test_generate_summary(mock_call_openrouter_api):
    # Setup
    transcript = "This is a test transcript."
    model = "openai/gpt-4o-mini"
    mock_call_openrouter_api.return_value = "This is a summary."

    # Execute
    result = generate_summary(transcript, model)

    # Verify
    assert result == "This is a summary."

    # Check that call_openrouter_api was called with the right prompt
    mock_call_openrouter_api.assert_called_once()
    args, kwargs = mock_call_openrouter_api.call_args
    prompt = args[0]
    called_model = args[1]

    assert "This is a test transcript." in prompt
    assert "Please provide a comprehensive summary" in prompt
    assert called_model == model


@patch("app.call_openrouter_api")
def test_generate_summary_truncates_long_transcript(mock_call_openrouter_api):
    # Setup
    long_transcript = "A" * 10000
    model = "test-model"
    mock_call_openrouter_api.return_value = "Summary"

    # Execute
    generate_summary(long_transcript, model)

    # Verify
    mock_call_openrouter_api.assert_called_once()
    args, _ = mock_call_openrouter_api.call_args
    prompt = args[0]

    assert "A" * 8000 in prompt
    assert "A" * 8001 not in prompt
