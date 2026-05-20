## 2024-05-20 - Optimize Streamlit Network Requests
**Learning:** In Streamlit apps, network requests like API calls or scraping (e.g. `get_video_info_youtube_api` or `fetch_transcript_direct`) can cause significant slowdowns because Streamlit re-runs the entire script on every user interaction.
**Action:** Always wrap expensive network requests or API calls in Streamlit with `@st.cache_data`. Use `ttl` (e.g., `ttl=3600`) for data that might change over time but doesn't need to be perfectly real-time, to save API quotas and dramatically improve UI responsiveness on re-renders.
