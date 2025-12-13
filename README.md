# 🎥 YouTube Transcript Scraper with AI https://ai-youtube-scraper.streamlit.app

A powerful Streamlit application that extracts transcripts from YouTube videos and provides AI-powered features like summarization and chat, powered by OpenRouter.ai.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-FF6B6B?style=for-the-badge)

## ✨ Features

- 🎥 **YouTube Transcript Extraction**: Extract transcripts from any YouTube video with captions
- 🤖 **AI Summarization**: Generate comprehensive summaries using various AI models
- 💬 **AI Chat**: Ask questions about the video content with conversational AI
- 🔄 **Multiple AI Models**: Support for GPT-4, Claude, Gemini, Llama, and more via OpenRouter
- 💾 **Export Options**: Download transcripts and summaries as text files
- 📱 **Responsive UI**: Clean and intuitive Streamlit interface

## 🚀 Quick Start

### Local Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/youtube-transcript-scraper.git
cd youtube-transcript-scraper
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
```bash
streamlit run streamlit_youtube_scraper.py
```

4. **Open your browser** to `http://localhost:8501`

## 🔑 Configuration

### API Keys Setup

#### OpenRouter.ai API Key (Required for AI features)

1. Sign up at [OpenRouter.ai](https://openrouter.ai)
2. Get your API key from [https://openrouter.ai/keys](https://openrouter.ai/keys)
3. **Set it securely** using one of these methods:

   **Option A: Streamlit Secrets (Recommended for Local)**
   ```bash
   # Copy the example file
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   # Edit .streamlit/secrets.toml and add your key
   ```

   **Option B: Environment Variable**
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   ```

   **Option C: Enter in Sidebar** (temporary, session-only)

   📖 See [SECRETS_SETUP.md](SECRETS_SETUP.md) for detailed instructions.

#### YouTube Data API Key (Optional - for video metadata)

The YouTube Data API v3 allows you to see video information like title, description, views, likes, etc.

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **YouTube Data API v3**:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key
5. Add it to `.streamlit/secrets.toml`:
   ```toml
   YOUTUBE_API_KEY = "your-youtube-api-key-here"
   ```

**Note:** YouTube Data API is optional. The app works without it, but you won't see video metadata.

## 📦 Deployment

### Option 1: Streamlit Cloud (Recommended - Free)

1. **Push your code to GitHub**

2. **Go to [Streamlit Cloud](https://streamlit.io/cloud)**

3. **Sign in with GitHub** and click "New app"

4. **Configure your app**:
   - Select your repository
   - Branch: `main` (or your default branch)
   - Main file path: `streamlit_youtube_scraper.py`

5. **Add secrets** (optional):
   - Go to "Advanced settings"
   - Add secret: `OPENROUTER_API_KEY` = `your-api-key-here`
   - Users can still enter their own API key in the app

6. **Deploy!** Your app will be live at `https://your-app-name.streamlit.app`

### Option 2: Heroku

1. **Install Heroku CLI** and login

2. **Create a Procfile**:
```
web: streamlit run streamlit_youtube_scraper.py --server.port=$PORT --server.address=0.0.0.0
```

3. **Create `setup.sh`**:
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = \$PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

4. **Deploy**:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-app-name
heroku config:set OPENROUTER_API_KEY=your-api-key-here
git push heroku main
```

### Option 3: Docker

1. **Create `Dockerfile`**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "streamlit_youtube_scraper.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Build and run**:
```bash
docker build -t youtube-scraper .
docker run -p 8501:8501 youtube-scraper
```

## 📖 Usage

1. **Enter a YouTube video URL** in the input field
   - Supported formats:
     - `https://www.youtube.com/watch?v=VIDEO_ID`
     - `https://youtu.be/VIDEO_ID`
     - `https://www.youtube.com/embed/VIDEO_ID`

2. **Click "Get Transcript"** to extract the transcript

3. **Use AI features**:
   - **Summary Tab**: Generate an AI-powered summary
   - **Chat Tab**: Ask questions about the video content

4. **Download** transcripts and summaries as text files

## 🤖 Supported AI Models

The app supports all models available on OpenRouter, including:

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku
- **Google**: Gemini Pro
- **Meta**: Llama 3.1 70B Instruct
- And 100+ more models!

Select your preferred model from the sidebar.

## 🛠️ Technical Details

### Transcript Extraction

- Uses `youtube-transcript-api` for reliable transcript fetching
- Automatically detects video ID from various URL formats
- Falls back to direct scraping if the API method fails
- Supports both manual and auto-generated captions
- Handles multiple languages

### AI Integration

- Powered by OpenRouter.ai for access to multiple AI models
- Context-aware chat with conversation history
- Intelligent summarization with key point extraction
- Token-efficient prompts to minimize API costs

## 📋 Dependencies

- `streamlit>=1.28.0` - Web framework
- `youtube-transcript-api>=0.6.0` - YouTube transcript extraction
- `requests>=2.31.0` - HTTP requests
- `google-api-python-client>=2.100.0` - YouTube Data API v3 (optional, for video metadata)

## ⚠️ Limitations

- Videos must have captions/transcripts enabled
- Some videos may not have transcripts available
- API usage costs depend on your OpenRouter plan
- Transcript length may be limited for very long videos

## 🐛 Troubleshooting

### Transcript Not Found
- Ensure the video has captions/transcripts enabled
- Try a different video that you know has captions
- Check if the video is publicly accessible

### API Errors
- Verify your OpenRouter API key is correct
- Check your API credit balance at [OpenRouter.ai](https://openrouter.ai)
- Ensure you have internet connectivity

### Installation Issues
- Make sure you're using Python 3.8 or higher
- Try upgrading packages: `pip install --upgrade -r requirements.txt`
- Use a virtual environment to avoid conflicts

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- AI powered by [OpenRouter.ai](https://openrouter.ai)
- YouTube transcript extraction using [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ using Streamlit and OpenRouter.ai**

If you find this project useful, please give it a ⭐ on GitHub!


