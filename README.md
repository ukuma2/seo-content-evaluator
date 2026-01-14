# 🔍 Advanced SEO Content Evaluator

A powerful Streamlit application that analyzes webpage SEO using Google Gemini AI, LangChain, and live keyword research via DuckDuckGo.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🕷️ **Web Crawling**: Extracts page content, title, meta description, and H1 tags
- 🔎 **Live Keyword Research**: Uses DuckDuckGo to find real-time keyword ideas
- 🤖 **AI-Powered Analysis**: Google Gemini analyzes content against strict SEO rules
- ✨ **Actionable Improvements**: Provides copy-paste ready title tags, meta descriptions, and intro paragraphs
- 📊 **SEO Scoring**: 0-100 score with critical issues identification

## Tech Stack

- **UI**: Streamlit
- **LLM Orchestration**: LangChain (LCEL)
- **AI Model**: Google Gemini (configurable: gemini-2.5-flash, gemini-3-flash-preview, gemini-3-pro-preview)
- **Web Crawler**: WebBaseLoader (LangChain Community)
- **Keyword Research**: DuckDuckGoSearchRun (LangChain Community)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/seo-agent-v2.git
   cd seo-agent-v2
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API Key** (Local):
   
   Create `.streamlit/secrets.toml`:
   ```bash
   # Windows PowerShell
   New-Item -Path .streamlit\secrets.toml -ItemType File
   
   # Linux/Mac
   touch .streamlit/secrets.toml
   ```
   
   Add your Google API key:
   ```toml
   GOOGLE_API_KEY = "your-google-api-key-here"
   ```
   
   **Get your Google API Key**: [Google AI Studio](https://makersuite.google.com/app/apikey)

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

### ☁️ Deploy to Streamlit Cloud (GitHub)

**Perfect for GitHub Student Developer Pack users!**

1. **Push to GitHub** (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set Main file: `app.py`
   - Add secret `GOOGLE_API_KEY` in app settings
   - Deploy! 🎉

📖 **Detailed deployment guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## Usage

1. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

2. **Enter a URL** in the input field (must be HTTP or HTTPS)

3. **Click "Analyze SEO"** and wait for the analysis to complete

4. **Review the results**:
   - SEO Score (0-100)
   - Critical issues
   - Recommended keywords
   - Copy-paste improvements for title, meta description, and intro paragraph

## How It Works

### Phase 1: Crawling
- Uses `WebBaseLoader` with a realistic User-Agent header
- Extracts main text content, title tag, meta description, and H1
- Caches results per URL to avoid redundant requests

### Phase 2: Keyword Research
- Uses Gemini to summarize page topic (3-6 words)
- Runs DuckDuckGo searches with multiple query patterns:
  - "primary keyword for {topic}"
  - "{topic} best practices 2026"
  - "people also ask {topic}"
- Extracts keyword candidates and source links from search results
- **Note**: This produces SERP-derived keyword ideas, not authoritative keyword volume data

### Phase 3: AI Analysis
- Sends extracted content and keyword ideas to Gemini
- Analyzes against modern SEO ranking factors:
  - Keyword placement (Title/H1/first 100 words)
  - Keyword density (1-2% target)
  - Readability and user experience
- Outputs structured JSON with:
  - SEO score (0-100)
  - 3 critical issues
  - Primary keyword + 5 secondary keywords
  - New title tag (≤60 chars)
  - New meta description (≤160 chars)
  - Rewritten intro paragraph
  - Suggested H1 (if missing/weak)

### Phase 4: Results Display
- Visual SEO score with progress bar
- Bulleted critical issues
- Copy-paste ready improvements in code blocks
- Keyword recommendations
- Source links from research

## Configuration

### Model Selection
Choose from the sidebar:
- **gemini-2.5-flash** (default) - Fast and efficient
- **gemini-3-flash-preview** - Latest flash model
- **gemini-3-pro-preview** - Most capable model

### Security Notes
- API key is stored in `.streamlit/secrets.toml` (not committed to git)
- Add `.streamlit/secrets.toml` to your `.gitignore` file
- Never share your API key publicly

## Troubleshooting

### "API Key Missing" Error
- Ensure `.streamlit/secrets.toml` exists and contains `GOOGLE_API_KEY`
- Restart Streamlit after creating/editing secrets.toml

### Crawl Errors
- **403 Forbidden**: Website blocked the crawler (try a different page)
- **Timeout**: Website took too long to respond
- **Empty Content**: Page may require JavaScript rendering (WebBaseLoader doesn't execute JS)

### Analysis Errors
- Check your API key is valid and has quota remaining
- Ensure you're using a supported Gemini model (not gemini-1.5-pro, which is deprecated)
- Try a shorter URL or simpler page if token limits are exceeded

## Limitations

- **JavaScript Rendering**: WebBaseLoader doesn't execute JavaScript, so JS-rendered content won't be captured
- **Keyword Volume**: DuckDuckGo provides SERP-derived ideas, not official search volume data
- **Rate Limits**: Be mindful of API rate limits for both Gemini and DuckDuckGo
- **Content Length**: Very long pages (>8000 chars) are truncated for analysis

## 📦 GitHub Deployment

This app is ready to deploy on **Streamlit Cloud** (free with GitHub Student Pack):

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app" → Select your repo
   - Add `GOOGLE_API_KEY` in Secrets
   - Deploy!

📖 **Full guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [Google Gemini](https://ai.google.dev)
- Uses [LangChain](https://www.langchain.com) for LLM orchestration
- Keyword research via [DuckDuckGo](https://duckduckgo.com)

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
3. Open an issue on GitHub
4. Verify your API key and model selection
