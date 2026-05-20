import pytest
from app import extract_video_id

def test_extract_video_id_standard():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_short_url():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_embed_url():
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_shorts_url():
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_with_query_params():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

def test_extract_video_id_invalid_url():
    url = "https://www.example.com"
    assert extract_video_id(url) is None

def test_extract_video_id_empty_string():
    url = ""
    assert extract_video_id(url) is None

def test_extract_video_id_none():
    with pytest.raises(TypeError):
        extract_video_id(None)
