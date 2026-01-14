# Deployment Guide: Streamlit Cloud (GitHub)

This guide will help you deploy the SEO Content Evaluator to Streamlit Cloud using your GitHub account.

## Prerequisites

- GitHub account (with Student Developer Pack if available)
- Google API Key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Repository pushed to GitHub

## Step-by-Step Deployment

### 1. Push to GitHub

If you haven't already, push your code to GitHub:

```bash
git init
git add .
git commit -m "Initial commit: SEO Content Evaluator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

**Important:** Make sure `.streamlit/secrets.toml` is in your `.gitignore` (it should be already).

### 2. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app"
   - Select your repository
   - Choose the branch (usually `main`)
   - Set Main file path: `app.py`

3. **Configure Secrets**
   - Click "Advanced settings" or go to app settings
   - Navigate to "Secrets" tab
   - Add your Google API key:
     ```
     GOOGLE_API_KEY = "your-actual-api-key-here"
     ```
   - Click "Save"

4. **Deploy**
   - Click "Deploy" or "Save"
   - Wait for the app to build and deploy (usually 1-2 minutes)
   - Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

## GitHub Student Developer Pack Benefits

If you have the GitHub Student Developer Pack:
- **Streamlit Cloud**: Free tier includes unlimited public apps
- **Google Cloud**: $50 credit for API usage
- **Other benefits**: Check your [GitHub Education](https://education.github.com/pack) dashboard

## Troubleshooting

### Build Fails
- Check that `requirements.txt` includes all dependencies
- Verify Python version compatibility (Streamlit Cloud uses Python 3.9+)
- Check build logs in Streamlit Cloud dashboard

### App Crashes on Startup
- Verify secrets are set correctly in Streamlit Cloud
- Check that `GOOGLE_API_KEY` matches exactly (case-sensitive)
- Review app logs in Streamlit Cloud dashboard

### API Errors
- Verify your Google API key is valid
- Check API quota/limits in Google Cloud Console
- Ensure billing is set up if required

### Import Errors
- Ensure all packages in `requirements.txt` are available on PyPI
- Check for version conflicts
- Review error logs for specific missing modules

## Environment Variables

Streamlit Cloud automatically handles:
- ✅ Secrets management (via Secrets tab)
- ✅ Python environment setup
- ✅ Dependency installation from `requirements.txt`

## Updating Your App

1. Make changes locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push
   ```
3. Streamlit Cloud will automatically redeploy (usually within 1-2 minutes)

## Custom Domain (Optional)

Streamlit Cloud free tier includes:
- Custom subdomain: `YOUR_APP_NAME.streamlit.app`
- You can also use your own domain (requires configuration)

## Monitoring

- **Logs**: Available in Streamlit Cloud dashboard
- **Usage**: Check your Streamlit Cloud account dashboard
- **Errors**: View real-time logs in the app dashboard

## Security Best Practices

1. ✅ Never commit `secrets.toml` to GitHub (already in `.gitignore`)
2. ✅ Use Streamlit Cloud Secrets for API keys
3. ✅ Rotate API keys periodically
4. ✅ Monitor API usage in Google Cloud Console
5. ✅ Set up API key restrictions in Google Cloud Console

## Support

- **Streamlit Cloud Docs**: [docs.streamlit.io/streamlit-cloud](https://docs.streamlit.io/streamlit-cloud)
- **GitHub Student Pack**: [education.github.com](https://education.github.com/pack)
- **Streamlit Community**: [discuss.streamlit.io](https://discuss.streamlit.io)
