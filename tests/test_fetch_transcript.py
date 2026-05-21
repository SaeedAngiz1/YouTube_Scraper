import pytest
from unittest.mock import patch, MagicMock
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)
import app
import json


def test_fetch_transcript_method_1_success():
    """Test Method 1 (youtube_transcript_api) successfully fetching transcript."""
    mock_transcript_data = [{"text": "Hello"}, {"text": "world"}]

    mock_yt_module = MagicMock()
    mock_yt_module.YouTubeTranscriptApi.get_transcript.return_value = (
        mock_transcript_data
    )

    with patch.dict("sys.modules", {"youtube_transcript_api": mock_yt_module}):
        app.fetch_transcript_direct.clear()
        result = app.fetch_transcript_direct("dummy_id")

        assert result == "Hello world"
        mock_yt_module.YouTubeTranscriptApi.get_transcript.assert_called_once_with(
            "dummy_id", languages=["en", "en-US", "en-GB"]
        )


def test_fetch_transcript_method_2_success():
    """Test Method 2 (Alternative API) successfully fetching transcript after Method 1 fails."""
    mock_yt_module = MagicMock()
    mock_yt_module.YouTubeTranscriptApi.get_transcript.side_effect = NoTranscriptFound(
        "dummy_id", "dummy_lang", "dummy_data"
    )
    # Prevent the fallback block in Method 1 from intercepting the logic!
    del mock_yt_module.YouTubeTranscriptApi.list_transcripts

    mock_yt_module._errors.NoTranscriptFound = NoTranscriptFound
    mock_yt_module._errors.TranscriptsDisabled = TranscriptsDisabled
    mock_yt_module._errors.VideoUnavailable = VideoUnavailable

    with patch.dict(
        "sys.modules",
        {
            "youtube_transcript_api": mock_yt_module,
            "youtube_transcript_api._errors": mock_yt_module._errors,
        },
    ):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Ensure the text is a real string and contains valid XML so app.py's internal ElementTree parses it successfully!
            mock_response.text = '<?xml version="1.0" encoding="utf-8" ?><transcript><text start="0" dur="1">Alternative</text><text start="1" dur="1">API</text></transcript>'
            mock_get.return_value = mock_response

            app.fetch_transcript_direct.clear()

            result = app.fetch_transcript_direct("dummy_id")

            assert result == "Alternative API"
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert "api/timedtext" in args[0]


def test_fetch_transcript_method_3_success():
    """Test Method 3 (Direct scraping) successfully fetching transcript after Methods 1 & 2 fail."""
    import xml.etree.ElementTree as ET

    mock_yt_module = MagicMock()
    mock_yt_module.YouTubeTranscriptApi.get_transcript.side_effect = NoTranscriptFound(
        "dummy_id", "dummy_lang", "dummy_data"
    )
    # Prevent the fallback block in Method 1 from intercepting the logic!
    del mock_yt_module.YouTubeTranscriptApi.list_transcripts

    mock_yt_module._errors.NoTranscriptFound = NoTranscriptFound
    mock_yt_module._errors.TranscriptsDisabled = TranscriptsDisabled
    mock_yt_module._errors.VideoUnavailable = VideoUnavailable

    with patch.dict(
        "sys.modules",
        {
            "youtube_transcript_api": mock_yt_module,
            "youtube_transcript_api._errors": mock_yt_module._errors,
        },
    ):
        with patch("requests.get") as mock_get:
            mock_method_2_response = MagicMock()
            mock_method_2_response.status_code = 404
            mock_method_2_response.text = ""

            mock_method_3_video_response = MagicMock()
            mock_method_3_video_response.status_code = 200
            # We use json.dumps to construct the inner string properly
            mock_method_3_video_response.text = f'"captionTracks": {json.dumps([{"baseUrl": "http://example.com/captions"}])}'

            mock_method_3_caption_response = MagicMock()
            mock_method_3_caption_response.status_code = 200
            # JSON format that the parser falls back to
            mock_method_3_caption_response.text = '{"events": [{"segs": [{"utf8": "Scraped "}]}, {"segs": [{"utf8": "Captions"}]}]}'

            # Since the json captions doesn't parse perfectly via ET, we need to ensure the ET.ParseError is thrown
            # to fall back to the JSON parsing. We can safely mock `ET.fromstring` here because we specifically want it to raise.
            with patch("xml.etree.ElementTree.fromstring") as mock_et:
                mock_et.side_effect = ET.ParseError("Not XML")

                mock_get.side_effect = [
                    mock_method_2_response,  # Method 2
                    mock_method_3_video_response,  # Method 3 - fetch video
                    mock_method_3_caption_response,  # Method 3 - fetch captions
                ]

                app.fetch_transcript_direct.clear()
                result = app.fetch_transcript_direct("dummy_id")

                assert result == "Scraped  Captions"
                assert mock_get.call_count == 3


def test_fetch_transcript_all_methods_fail():
    """Test behavior when all methods fail."""
    mock_yt_module = MagicMock()
    mock_yt_module.YouTubeTranscriptApi.get_transcript.side_effect = Exception(
        "Method 1 failed"
    )
    # Prevent the fallback block in Method 1 from intercepting the logic!
    del mock_yt_module.YouTubeTranscriptApi.list_transcripts

    mock_yt_module._errors.NoTranscriptFound = NoTranscriptFound
    mock_yt_module._errors.TranscriptsDisabled = TranscriptsDisabled
    mock_yt_module._errors.VideoUnavailable = VideoUnavailable

    with patch.dict(
        "sys.modules",
        {
            "youtube_transcript_api": mock_yt_module,
            "youtube_transcript_api._errors": mock_yt_module._errors,
        },
    ):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")

            with patch("app.st.warning") as mock_warning:
                app.fetch_transcript_direct.clear()
                result = app.fetch_transcript_direct("dummy_id")

                assert result is None
                mock_warning.assert_called_once()
                assert (
                    "All transcript fetching methods failed"
                    in mock_warning.call_args[0][0]
                )
