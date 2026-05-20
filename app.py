import streamlit as st
import re
import requests
from typing import List, Dict, Optional
import os

# YouTube Data API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="YouTube Transcript Scraper with AI",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "transcript" not in st.session_state:
    st.session_state.transcript = ""
if "video_id" not in st.session_state:
    st.session_state.video_id = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Pre-compile regex patterns for better performance
YOUTUBE_URL_PATTERNS = [
    re.compile(
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([^&\n?#]+)"
    ),
    re.compile(r"youtube\.com\/watch\?.*v=([^&\n?#]+)"),
]


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    for pattern in YOUTUBE_URL_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    return None


@st.cache_data(ttl=3600)
def get_video_info_youtube_api(
    video_id: str, api_key: Optional[str] = None
) -> Optional[Dict]:
    """Get video information using YouTube Data API v3."""
    if not YOUTUBE_API_AVAILABLE:
        return None

    # Get API key from secrets, environment, or session state
    if not api_key:
        try:
            api_key = st.secrets.get("YOUTUBE_API_KEY", None)
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        return None

    try:
        # Build YouTube API service
        youtube = build("youtube", "v3", developerKey=api_key)

        # Get video details
        request = youtube.videos().list(
            part="snippet,statistics,contentDetails", id=video_id
        )
        response = request.execute()

        if response.get("items"):
            item = response["items"][0]
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content_details = item.get("contentDetails", {})

            return {
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail": snippet.get("thumbnails", {})
                .get("high", {})
                .get("url", ""),
                "view_count": statistics.get("viewCount", "0"),
                "like_count": statistics.get("likeCount", "0"),
                "comment_count": statistics.get("commentCount", "0"),
                "duration": content_details.get("duration", ""),
                "tags": snippet.get("tags", []),
                "category_id": snippet.get("categoryId", ""),
            }
    except HttpError as e:
        st.warning(f"YouTube Data API error: {e}")
    except Exception as e:
        st.warning(f"Error fetching video info: {str(e)}")

    return None


@st.cache_data
def fetch_transcript_direct(video_id: str) -> Optional[str]:
    """Fetch transcript directly from YouTube using multiple methods."""
    error_messages = []

    # Method 1: Try youtube-transcript-api package (most reliable)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )

        try:
            # Try simple get_transcript first (works for most cases)
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en", "en-US", "en-GB"]
                )
                return " ".join([item["text"] for item in transcript_data])
            except (NoTranscriptFound, TranscriptsDisabled):
                # Try with any available language
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
                    return " ".join([item["text"] for item in transcript_data])
                except (NoTranscriptFound, TranscriptsDisabled):
                    # Try list_transcripts if available (newer API)
                    try:
                        if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                            transcript_list = YouTubeTranscriptApi.list_transcripts(
                                video_id
                            )

                            # Try to get English transcript first
                            try:
                                transcript = transcript_list.find_transcript(
                                    ["en", "en-US", "en-GB"]
                                )
                                transcript_data = transcript.fetch()
                                return " ".join(
                                    [item["text"] for item in transcript_data]
                                )
                            except (NoTranscriptFound, TranscriptsDisabled):
                                # If English fails, try auto-generated English
                                try:
                                    transcript = (
                                        transcript_list.find_generated_transcript(
                                            ["en"]
                                        )
                                    )
                                    transcript_data = transcript.fetch()
                                    return " ".join(
                                        [item["text"] for item in transcript_data]
                                    )
                                except (NoTranscriptFound, TranscriptsDisabled):
                                    # Get the first available transcript (manual or auto-generated)
                                    for transcript in transcript_list:
                                        try:
                                            transcript_data = transcript.fetch()
                                            return " ".join(
                                                [
                                                    item["text"]
                                                    for item in transcript_data
                                                ]
                                            )
                                        except Exception:
                                            continue
                    except AttributeError:
                        # list_transcripts not available in this version
                        pass
        except VideoUnavailable:
            error_messages.append("Video is unavailable or does not exist")
        except TranscriptsDisabled:
            error_messages.append("Transcripts are disabled for this video")
        except NoTranscriptFound:
            error_messages.append("No transcripts found for this video")
        except Exception as e:
            error_messages.append(f"youtube-transcript-api error: {str(e)}")

    except ImportError:
        st.error(
            "⚠️ youtube-transcript-api package not installed. Please run: pip install youtube-transcript-api"
        )
        return None
    except Exception as e:
        error_messages.append(f"Package error: {str(e)}")

    # Method 2: Alternative API endpoint
    try:
        # Try using YouTube's internal API
        api_url = f"https://www.youtube.com/api/timedtext?lang=en&v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/xml, text/xml, */*",
        }
        response = requests.get(api_url, headers=headers, timeout=15)

        if response.status_code == 200 and response.text.strip():
            # Parse XML transcript
            import defusedxml.ElementTree as ET

            try:
                root = ET.fromstring(response.text)
                texts = []
                for elem in root.iter():
                    if elem.text and elem.text.strip():
                        texts.append(elem.text.strip())
                if texts:
                    return " ".join(texts)
            except ET.ParseError:
                # Try parsing as JSON if XML fails
                pass
    except Exception as e:
        error_messages.append(f"Alternative API method failed: {str(e)}")

    # Method 3: Direct scraping fallback (improved)
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        response = requests.get(video_url, headers=headers, timeout=15)

        if response.status_code != 200:
            error_messages.append(
                f"Failed to fetch video page (status: {response.status_code})"
            )
        else:
            # Try multiple patterns to find caption tracks
            patterns = [
                r'"captionTracks":\s*(\[.*?\])',
                r'"captions":\s*\{[^}]*"captionTracks":\s*(\[.*?\])',
                r'captionTracks["\']?\s*:\s*(\[.*?\])',
            ]

            captions = None
            for pattern in patterns:
                caption_match = re.search(pattern, response.text, re.DOTALL)
                if caption_match:
                    try:
                        import json

                        captions = json.loads(caption_match.group(1))
                        break
                    except json.JSONDecodeError:
                        continue

            if captions and len(captions) > 0:
                # Try each caption track
                for caption in captions:
                    caption_url = caption.get("baseUrl") or caption.get("url")
                    if caption_url:
                        try:
                            caption_response = requests.get(
                                caption_url, headers=headers, timeout=15
                            )
                            if (
                                caption_response.status_code == 200
                                and caption_response.text.strip()
                            ):
                                # Try XML parsing
                                import defusedxml.ElementTree as ET

                                try:
                                    root = ET.fromstring(caption_response.text)
                                    texts = []
                                    for elem in root.iter():
                                        if elem.text and elem.text.strip():
                                            texts.append(elem.text.strip())
                                    if texts:
                                        return " ".join(texts)
                                except ET.ParseError:
                                    # If XML parsing fails, try to extract text from response
                                    # Sometimes YouTube returns JSON instead of XML
                                    try:
                                        import json

                                        json_data = json.loads(caption_response.text)
                                        # Extract text from JSON structure if available
                                        if isinstance(json_data, dict):
                                            events = json_data.get("events", [])
                                            texts = []
                                            for event in events:
                                                if "segs" in event:
                                                    for seg in event["segs"]:
                                                        if "utf8" in seg:
                                                            texts.append(seg["utf8"])
                                            if texts:
                                                return " ".join(texts)
                                    except Exception:
                                        pass
                        except Exception:
                            continue
    except Exception as e:
        error_messages.append(f"Scraping method failed: {str(e)}")

    # If all methods failed, show helpful error message
    if error_messages:
        st.warning(
            "⚠️ All transcript fetching methods failed. This video may not have captions enabled."
        )
        with st.expander("🔍 Show technical details"):
            st.code("\n".join(error_messages))

    return None


def call_openrouter_api(
    prompt: str, model: str = "openai/gpt-4o-mini"
) -> Optional[str]:
    """Call OpenRouter.ai API for AI responses."""
    # Try to get API key from multiple sources (in order of priority):
    # 1. Session state (user entered in sidebar)
    # 2. Streamlit secrets (for production)
    # 3. Environment variable (for local development)

    secrets_key = None
    try:
        secrets_key = st.secrets.get("OPENROUTER_API_KEY", None)
    except (FileNotFoundError, KeyError):
        # Secrets file doesn't exist or key not found - that's okay
        pass

    api_key = (
        st.session_state.get("openrouter_api_key")
        or secrets_key
        or os.getenv("OPENROUTER_API_KEY")
    )

    if not api_key:
        st.error(
            "OpenRouter API key not found. Please set it in the sidebar, in .streamlit/secrets.toml, or as OPENROUTER_API_KEY environment variable."
        )
        return None

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com",
                "X-Title": "YouTube Transcript Scraper with AI",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error calling OpenRouter API: {str(e)}")
        return None


def generate_summary(transcript: str, model: str) -> str:
    """Generate AI summary of the transcript."""
    # Limit transcript to first 8000 chars to avoid token limits
    transcript_snippet = transcript[:8000]

    prompt = f"""Please provide a comprehensive summary of the following YouTube video transcript. Include:
1. Main topics and key points discussed
2. Important details and insights
3. Any conclusions or takeaways
4. Structure the summary in clear paragraphs

TRANSCRIPT:
{transcript_snippet}

SUMMARY:"""

    return call_openrouter_api(prompt, model)


def chat_with_transcript(
    question: str, transcript: str, model: str, chat_history: List[Dict]
) -> str:
    """Chat with AI about the transcript."""
    # Build context from transcript (limit to 6000 chars)
    context = transcript[:6000]

    # Build conversation history
    conversation_context = ""
    if chat_history:
        recent_history = chat_history[-5:]  # Last 5 messages
        conversation_context = "\n\nRecent conversation:\n"
        for msg in recent_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_context += f"{role}: {msg['content']}\n"

    prompt = f"""You are a helpful AI assistant that has access to a YouTube video transcript. Answer the user's question based on the following video transcript.

VIDEO TRANSCRIPT:
{context}

{conversation_context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer based on the video transcript provided above
- Be concise but thorough
- If the information isn't in the transcript, say so
- Use natural, conversational language
- Reference specific details from the transcript when relevant

ANSWER:"""

    return call_openrouter_api(prompt, model)


# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")

    # OpenRouter API Key
    # Check if API key exists in secrets or environment
    secrets_key = None
    try:
        secrets_key = st.secrets.get("OPENROUTER_API_KEY", "")
    except (FileNotFoundError, KeyError):
        # Secrets file doesn't exist or key not found - that's okay
        pass

    default_key = (
        st.session_state.get("openrouter_api_key", "")
        or secrets_key
        or os.getenv("OPENROUTER_API_KEY", "")
    )

    if default_key and not st.session_state.get("openrouter_api_key"):
        # If key exists in secrets/env but not session state, set it
        st.session_state.openrouter_api_key = default_key
        st.info("✅ API key loaded from secrets/environment")

    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        value=st.session_state.get("openrouter_api_key", ""),
        help="Get your API key from https://openrouter.ai/keys. You can also set it in .streamlit/secrets.toml for local use.",
    )
    st.session_state.openrouter_api_key = api_key

    # YouTube Data API Key (optional - for video metadata)
    st.divider()
    st.subheader("📺 YouTube Data API (Optional)")
    youtube_api_key_help = "Get your API key from https://console.cloud.google.com/apis/credentials. Optional - enables video metadata display."

    youtube_secrets_key = None
    try:
        youtube_secrets_key = st.secrets.get("YOUTUBE_API_KEY", "")
    except (FileNotFoundError, KeyError):
        pass

    youtube_default_key = (
        st.session_state.get("youtube_api_key", "")
        or youtube_secrets_key
        or os.getenv("YOUTUBE_API_KEY", "")
    )

    if youtube_default_key and not st.session_state.get("youtube_api_key"):
        st.session_state.youtube_api_key = youtube_default_key

    youtube_api_key = st.text_input(
        "YouTube Data API Key (Optional)",
        type="password",
        value=st.session_state.get("youtube_api_key", ""),
        help=youtube_api_key_help,
    )
    st.session_state.youtube_api_key = youtube_api_key

    if YOUTUBE_API_AVAILABLE:
        st.caption("✅ YouTube Data API library installed")
    else:
        st.warning("⚠️ Install: pip install google-api-python-client")

    # Model selection
    st.subheader("🤖 AI Model")
    model = st.selectbox(
        "Choose AI Model",
        options=[
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-pro",
            "meta-llama/llama-3.1-70b-instruct",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-3-27b-it:free",
        ],
        index=0,
        help="Select the AI model to use for summaries and chat",
    )

    st.divider()

    # Instructions
    st.subheader("📖 How to Use")
    st.markdown("""
    1. Enter a YouTube video URL
    2. Click "Get Transcript"
    3. Use AI features:
       - Generate summary
       - Chat about the video
    """)

    st.divider()

    # Clear button
    if st.button("🗑️ Clear All", type="secondary"):
        st.session_state.transcript = ""
        st.session_state.video_id = ""
        st.session_state.chat_history = []
        st.rerun()


# Main content
st.title("🎥 YouTube Transcript Scraper with AI")
st.markdown(
    "Extract transcripts from YouTube videos and interact with them using AI powered by OpenRouter.ai"
)

# URL input
url_input = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Enter any YouTube video URL (watch, short, embed formats supported)",
)

col1, col2 = st.columns([1, 4])

with col1:
    fetch_button = st.button(
        "📥 Get Transcript", type="primary", use_container_width=True
    )

# Fetch transcript
if fetch_button:
    if not url_input:
        st.error("Please enter a YouTube URL")
    else:
        video_id = extract_video_id(url_input)
        if not video_id:
            st.error("Invalid YouTube URL. Please check the URL and try again.")
        else:
            with st.spinner(
                "Fetching video information and transcript... This may take a moment."
            ):
                st.session_state.video_id = video_id

                # Get video metadata using YouTube Data API (if available)
                video_info = None
                if YOUTUBE_API_AVAILABLE and st.session_state.get("youtube_api_key"):
                    try:
                        video_info = get_video_info_youtube_api(
                            video_id, st.session_state.get("youtube_api_key")
                        )
                        if video_info:
                            st.session_state.video_info = video_info
                    except Exception as e:
                        st.warning(f"Could not fetch video metadata: {str(e)}")

                # Fetch transcript
                transcript = fetch_transcript_direct(video_id)

                if transcript:
                    st.session_state.transcript = transcript
                    st.success(
                        f"✅ Transcript fetched successfully! ({len(transcript)} characters)"
                    )
                else:
                    st.error(
                        "Failed to fetch transcript. The video may not have captions/transcripts enabled."
                    )

# Display video information if available
if st.session_state.get("video_info"):
    st.divider()
    video_info = st.session_state.video_info

    col1, col2 = st.columns([1, 2])
    with col1:
        if video_info.get("thumbnail"):
            st.image(video_info["thumbnail"], use_container_width=True)

    with col2:
        st.subheader(video_info.get("title", "Video Information"))
        if video_info.get("channel_title"):
            st.write(f"**Channel:** {video_info['channel_title']}")
        if video_info.get("view_count"):
            try:
                view_count = int(video_info["view_count"])
                st.write(f"**Views:** {view_count:,}")
            except (ValueError, TypeError):
                st.write(f"**Views:** {video_info['view_count']}")
        if video_info.get("like_count"):
            try:
                like_count = int(video_info["like_count"])
                st.write(f"**Likes:** {like_count:,}")
            except (ValueError, TypeError):
                st.write(f"**Likes:** {video_info['like_count']}")
        if video_info.get("published_at"):
            from datetime import datetime

            try:
                pub_date = datetime.fromisoformat(
                    video_info["published_at"].replace("Z", "+00:00")
                )
                st.write(f"**Published:** {pub_date.strftime('%B %d, %Y')}")
            except Exception:
                st.write(f"**Published:** {video_info['published_at']}")
        if video_info.get("description"):
            with st.expander("📝 Video Description"):
                st.write(
                    video_info["description"][:500] + "..."
                    if len(video_info["description"]) > 500
                    else video_info["description"]
                )

# Display transcript and AI features
# Show tabs if we have transcript OR video info (for chat with description)
has_content = st.session_state.transcript or st.session_state.get("video_info")

if has_content:
    st.divider()

    # Determine which tabs to show
    if st.session_state.transcript:
        # Tabs for different views when transcript is available
        tab1, tab2, tab3 = st.tabs(["📄 Transcript", "📝 AI Summary", "💬 AI Chat"])
    else:
        # Only show chat and summary tabs if no transcript but we have video info
        tab1, tab2 = st.tabs(["💬 AI Chat", "📝 AI Summary"])
        tab3 = None  # No transcript tab

    # Transcript tab (only if transcript exists)
    if st.session_state.transcript and tab1 is not None:
        with tab1:
            st.subheader("Video Transcript")
            st.text_area(
                "Full Transcript",
                value=st.session_state.transcript,
                height=400,
                disabled=True,
                label_visibility="collapsed",
            )
            st.download_button(
                "💾 Download Transcript",
                data=st.session_state.transcript,
                file_name=f"transcript_{st.session_state.video_id}.txt",
                mime="text/plain",
            )

    # Summary tab
    summary_tab = tab2 if st.session_state.transcript else tab1
    with summary_tab:
        st.subheader("AI Summary")

        # Use transcript if available, otherwise use video description
        content_for_summary = st.session_state.transcript
        if not content_for_summary and st.session_state.get("video_info"):
            content_for_summary = st.session_state["video_info"].get("description", "")
            if content_for_summary:
                st.info(
                    "ℹ️ Generating summary from video description (transcript not available)"
                )

        if content_for_summary:
            if st.button("✨ Generate Summary", type="primary"):
                if not api_key:
                    st.error(
                        "Please enter your OpenRouter API key in the sidebar first."
                    )
                else:
                    with st.spinner("Generating AI summary... This may take a moment."):
                        summary = generate_summary(content_for_summary, model)
                        if summary:
                            st.session_state.summary = summary
                            st.write(summary)
                            st.download_button(
                                "💾 Download Summary",
                                data=summary,
                                file_name=f"summary_{st.session_state.video_id}.txt",
                                mime="text/plain",
                            )
                        else:
                            st.error(
                                "Failed to generate summary. Please check your API key and try again."
                            )
            else:
                if "summary" in st.session_state:
                    st.write(st.session_state.summary)
        else:
            st.warning(
                "No content available for summary. Please fetch a transcript or video information."
            )

    # Chat tab
    if st.session_state.transcript:
        chat_tab = tab3
    else:
        chat_tab = tab1  # Chat is first tab when no transcript
    with chat_tab:
        st.subheader("Chat with AI about the Video")

        # Determine content source for chat
        chat_content = st.session_state.transcript
        if not chat_content and st.session_state.get("video_info"):
            video_info = st.session_state["video_info"]
            # Build context from video info
            chat_content = f"""
Video Title: {video_info.get('title', '')}
Channel: {video_info.get('channel_title', '')}
Description: {video_info.get('description', '')}
Views: {video_info.get('view_count', '')}
Likes: {video_info.get('like_count', '')}
Published: {video_info.get('published_at', '')}
"""
            st.info("ℹ️ Chatting using video information (transcript not available)")

        if chat_content:
            # Display chat history
            if st.session_state.chat_history:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

            # Chat input
            user_question = st.chat_input("Ask me anything about the video...")

            if user_question:
                if not api_key:
                    st.error(
                        "Please enter your OpenRouter API key in the sidebar first."
                    )
                else:
                    # Add user message to chat
                    st.session_state.chat_history.append(
                        {"role": "user", "content": user_question}
                    )

                    with st.chat_message("user"):
                        st.write(user_question)

                    # Get AI response
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            response = chat_with_transcript(
                                user_question,
                                chat_content,
                                model,
                                st.session_state.chat_history,
                            )

                            if response:
                                st.write(response)
                                st.session_state.chat_history.append(
                                    {"role": "assistant", "content": response}
                                )
                            else:
                                st.error(
                                    "Failed to get AI response. Please check your API key and try again."
                                )

                    st.rerun()
        else:
            st.warning(
                "No content available for chat. Please fetch a transcript or video information."
            )

else:
    # Instructions when no transcript
    st.info("👆 Enter a YouTube URL above and click 'Get Transcript' to get started!")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter.ai</a> |
        Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
