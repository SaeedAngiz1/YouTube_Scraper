from unittest.mock import patch
from app import chat_with_transcript

# Mock responses for tests
MOCK_API_RESPONSE = "This is a mock AI response."


@patch("app.call_openrouter_api")
def test_chat_with_transcript_basic_query(mock_call_api):
    """Test basic query with no chat history and a short transcript."""
    mock_call_api.return_value = MOCK_API_RESPONSE

    question = "What is this video about?"
    transcript = "This is a short video transcript."
    model = "test-model"
    chat_history = []

    result = chat_with_transcript(question, transcript, model, chat_history)

    assert result == MOCK_API_RESPONSE

    # Verify mock was called correctly
    mock_call_api.assert_called_once()
    call_args = mock_call_api.call_args[0]
    prompt = call_args[0]
    called_model = call_args[1]

    assert called_model == model
    assert question in prompt
    assert transcript in prompt
    assert "Recent conversation:" not in prompt


@patch("app.call_openrouter_api")
def test_chat_with_transcript_truncation(mock_call_api):
    """Test that long transcripts are correctly truncated to 6000 characters."""
    mock_call_api.return_value = MOCK_API_RESPONSE

    question = "Summary?"
    transcript = "A" * 7000  # Longer than 6000 chars
    model = "test-model"

    chat_with_transcript(question, transcript, model, [])

    call_args = mock_call_api.call_args[0]
    prompt = call_args[0]

    # 6000 chars of 'A' should be in the prompt
    assert "A" * 6000 in prompt
    # 6001 chars of 'A' should NOT be in the prompt (truncation happens)
    assert "A" * 6001 not in prompt


@patch("app.call_openrouter_api")
def test_chat_with_transcript_with_history(mock_call_api):
    """Test query with a short chat history."""
    mock_call_api.return_value = MOCK_API_RESPONSE

    question = "Follow up question?"
    transcript = "Transcript content."
    model = "test-model"
    chat_history = [
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"},
    ]

    chat_with_transcript(question, transcript, model, chat_history)

    call_args = mock_call_api.call_args[0]
    prompt = call_args[0]

    assert "Recent conversation:" in prompt
    assert "User: Previous question" in prompt
    assert "Assistant: Previous answer" in prompt


@patch("app.call_openrouter_api")
def test_chat_with_transcript_max_history(mock_call_api):
    """Test that only the last 5 messages are included in chat history."""
    mock_call_api.return_value = MOCK_API_RESPONSE

    question = "Follow up question?"
    transcript = "Transcript content."
    model = "test-model"
    chat_history = [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"},
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "Answer 2"},
        {"role": "user", "content": "Question 3"},
        {"role": "assistant", "content": "Answer 3"},
        {"role": "user", "content": "Question 4"},
    ]  # 7 messages total

    chat_with_transcript(question, transcript, model, chat_history)

    call_args = mock_call_api.call_args[0]
    prompt = call_args[0]

    assert "Recent conversation:" in prompt

    # The oldest 2 messages should NOT be in the prompt
    assert "User: Question 1" not in prompt
    assert "Assistant: Answer 1" not in prompt

    # The most recent 5 messages should be in the prompt
    assert "User: Question 2" in prompt
    assert "Assistant: Answer 2" in prompt
    assert "User: Question 3" in prompt
    assert "Assistant: Answer 3" in prompt
    assert "User: Question 4" in prompt
