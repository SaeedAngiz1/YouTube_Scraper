import pytest
from app import extract_video_id

def test_extract_video_id():
    # Regular watch URL
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Shortened URL
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Embed URL
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Shorts URL
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # URL with additional parameters before v
    assert extract_video_id("https://www.youtube.com/watch?foo=bar&v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # URL with additional parameters after v
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") == "dQw4w9WgXcQ"

    # URL without http/https
    assert extract_video_id("youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Invalid URLs
    assert extract_video_id("https://www.google.com") is None
    assert extract_video_id("not_a_url") is None
    assert extract_video_id("") is None
