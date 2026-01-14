# 🚀 Quick Start Guide

## For GitHub + Streamlit Cloud Deployment

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit: SEO Content Evaluator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Visit: https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Main file: `app.py`
6. Add secret: `GOOGLE_API_KEY` = `your-key-here`
7. Deploy!

**That's it!** Your app will be live in ~2 minutes.

## For Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets file
# Windows:
New-Item -Path .streamlit\secrets.toml -ItemType File

# Add your API key to .streamlit/secrets.toml:
# GOOGLE_API_KEY = "your-key-here"

# Run
streamlit run app.py
```

## Get Your Google API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Create API key
4. Copy and use in secrets

## Need Help?

- 📖 Full deployment: See [DEPLOYMENT.md](DEPLOYMENT.md)
- 🔧 Setup checklist: See [GITHUB_SETUP.md](GITHUB_SETUP.md)
- 🐛 Issues: Open on GitHub
