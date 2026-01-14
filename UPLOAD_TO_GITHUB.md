# 📤 How to Upload to GitHub

Simple step-by-step guide to upload your SEO Content Evaluator to GitHub.

## Method 1: Using Command Line (Recommended)

### Step 1: Open Terminal/PowerShell

- **Windows**: Press `Win + X` → Select "Windows PowerShell" or "Terminal"
- Navigate to your project folder:
  ```powershell
  cd "c:\Users\TechTeamUtkarsh\OneDrive - Greenhalgh Pickard\Desktop\Seo agent v2"
  ```

### Step 2: Initialize Git (if not already done)

```bash
git init
```

### Step 3: Check What Will Be Uploaded

```bash
git status
```

**Important**: Make sure `.streamlit/secrets.toml` is NOT listed. If it appears, it's already in `.gitignore` (which is correct).

### Step 4: Add All Files

```bash
git add .
```

### Step 5: Create First Commit

```bash
git commit -m "Initial commit: SEO Content Evaluator"
```

### Step 6: Create Repository on GitHub

1. Go to [github.com](https://github.com)
2. Sign in (or create account)
3. Click the **"+"** icon (top right) → **"New repository"**
4. Fill in:
   - **Repository name**: `seo-content-evaluator` (or any name you like)
   - **Description**: "Advanced SEO Content Evaluator using Gemini AI"
   - **Visibility**: Choose **Public** (required for free Streamlit Cloud)
   - **DO NOT** check "Initialize with README" (you already have files)
5. Click **"Create repository"**

### Step 7: Connect and Push

GitHub will show you commands. Use these:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

**Replace**:
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO_NAME` with the repository name you created

Example:
```bash
git remote add origin https://github.com/johndoe/seo-content-evaluator.git
git push -u origin main
```

### Step 8: Enter Credentials

- If prompted for username: Enter your GitHub username
- If prompted for password: Use a **Personal Access Token** (not your GitHub password)
  - Create token: GitHub → Settings → Developer settings → Personal access tokens → Generate new token
  - Or use GitHub Desktop (see Method 2 below)

## Method 2: Using GitHub Desktop (Easier)

### Step 1: Download GitHub Desktop

1. Go to [desktop.github.com](https://desktop.github.com)
2. Download and install GitHub Desktop
3. Sign in with your GitHub account

### Step 2: Add Your Project

1. Open GitHub Desktop
2. Click **"File"** → **"Add Local Repository"**
3. Click **"Choose..."** and select your project folder:
   ```
   c:\Users\TechTeamUtkarsh\OneDrive - Greenhalgh Pickard\Desktop\Seo agent v2
   ```
4. Click **"Add Repository"**

### Step 3: Commit Files

1. You'll see all your files listed
2. **Verify** `.streamlit/secrets.toml` is NOT listed (it should be grayed out)
3. At the bottom, type commit message: `"Initial commit: SEO Content Evaluator"`
4. Click **"Commit to main"**

### Step 4: Publish to GitHub

1. Click **"Publish repository"** button (top right)
2. Fill in:
   - **Name**: `seo-content-evaluator` (or your choice)
   - **Description**: "Advanced SEO Content Evaluator using Gemini AI"
   - **Keep this code private**: Uncheck (must be Public for free Streamlit Cloud)
3. Click **"Publish Repository"**

Done! Your code is now on GitHub! 🎉

## Verify Upload

1. Go to your GitHub profile: `https://github.com/YOUR_USERNAME`
2. You should see your new repository
3. Click on it to verify all files are there
4. **Important**: Check that `.streamlit/secrets.toml` is NOT visible (it should be hidden)

## Next Step: Deploy to Streamlit Cloud

Now that your code is on GitHub:

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repository
5. Main file: `app.py`
6. Add secret `GOOGLE_API_KEY` in settings
7. Deploy!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Troubleshooting

### "Repository already exists" Error
- You already have a remote. Remove it first:
  ```bash
  git remote remove origin
  ```
- Then add your new repository URL

### "Authentication failed" Error
- Use a Personal Access Token instead of password
- Or use GitHub Desktop (handles auth automatically)

### "Secrets file is visible on GitHub"
- If `.streamlit/secrets.toml` appears on GitHub:
  1. Remove it from GitHub (but keep local file):
     ```bash
     git rm --cached .streamlit/secrets.toml
     git commit -m "Remove secrets file"
     git push
     ```
  2. Verify `.gitignore` includes `.streamlit/secrets.toml`

### Files Not Appearing
- Make sure you ran `git add .`
- Check `git status` to see what's staged
- Verify you're in the correct directory

## Quick Reference Commands

```bash
# Check status
git status

# Add all files
git add .

# Commit
git commit -m "Your message here"

# Push to GitHub
git push origin main

# Check remote URL
git remote -v
```

## Need Help?

- 📖 Full deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
- 🔧 Setup checklist: [GITHUB_SETUP.md](GITHUB_SETUP.md)
- 🚀 Quick start: [QUICK_START.md](QUICK_START.md)
