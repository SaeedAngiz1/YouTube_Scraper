from app import fetch_transcript_direct
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
import requests


def test_fetch_transcript_direct_error_path_transcripts_disabled(mocker):
    mocker.patch(
        "app.requests.get",
        side_effect=requests.exceptions.RequestException("Network Error"),
    )
    mocker.patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        create=True,
        side_effect=TranscriptsDisabled("video_id"),
    )
    mocker.patch(
        "youtube_transcript_api.YouTubeTranscriptApi.list_transcripts",
        create=True,
        side_effect=TranscriptsDisabled("video_id"),
    )

    result = fetch_transcript_direct("video_id")
    assert result is None


def test_fetch_transcript_direct_error_path_no_transcript_found(mocker):
    mocker.patch(
        "app.requests.get",
        side_effect=requests.exceptions.RequestException("Network Error"),
    )
    # NoTranscriptFound requires video_id, requested_language_codes, transcript_data
    mocker.patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        create=True,
        side_effect=NoTranscriptFound("video_id", [], []),
    )
    mocker.patch(
        "youtube_transcript_api.YouTubeTranscriptApi.list_transcripts",
        create=True,
        side_effect=NoTranscriptFound("video_id", [], []),
    )

    result = fetch_transcript_direct("video_id")
    assert result is None


def test_fetch_transcript_direct_error_path_video_unavailable(mocker):
    mocker.patch(
        "app.requests.get",
        side_effect=requests.exceptions.RequestException("Network Error"),
    )
    mocker.patch(
        "youtube_transcript_api.YouTubeTranscriptApi.get_transcript",
        create=True,
        side_effect=VideoUnavailable("video_id"),
    )

    result = fetch_transcript_direct("video_id")
    assert result is None
