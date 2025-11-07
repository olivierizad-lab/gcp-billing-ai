# Fix GitHub Pages to Show GitBook Documentation

## The Problem

GitHub Pages is currently serving the root `README.md` file instead of the GitBook-built documentation. This happens when GitHub Pages is configured to serve from a branch instead of GitHub Actions.

## The Solution

### Step 1: Configure GitHub Pages Source

1. Go to your repository: https://github.com/olivierizad-lab/gcp-billing-ai
2. Click **Settings** (top right)
3. Scroll down to **Pages** (left sidebar)
4. Under **Source**, you'll see one of these options:
   - **"Deploy from a branch"** ← This is the problem!
   - **"GitHub Actions"** ← This is what we need!

5. **Change it to "GitHub Actions"**:
   - Click the dropdown under "Source"
   - Select **"GitHub Actions"**
   - Click **Save**

### Step 2: Create GitHub Pages Environment (if needed)

The workflow uses a `github-pages` environment. If it doesn't exist:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Name it: `github-pages`
4. Click **Configure environment**
5. Don't add any protection rules (leave defaults)
6. Click **Save protection rules**

### Step 3: Trigger the Workflow

1. Go to **Actions** tab
2. Click **Build and Deploy Documentation** workflow
3. Click **Run workflow** (top right)
4. Select branch: `main`
5. Click **Run workflow**

### Step 4: Wait for Deployment

- The workflow will take 2-3 minutes to build GitBook
- After completion, wait 1-2 minutes for GitHub Pages to update
- The site will be available at: https://olivierizad-lab.github.io/gcp-billing-ai/

## Verify It's Working

After the workflow completes:

1. Visit: https://olivierizad-lab.github.io/gcp-billing-ai/
2. You should see:
   - **Documentation Index** page (not README.md)
   - Navigation sidebar on the left
   - GitBook-styled documentation
   - Table of contents from `SUMMARY.md`

## Troubleshooting

### Still seeing README.md?

- **Clear browser cache**: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- **Wait 2-3 minutes** after workflow completion
- **Check workflow status**: Make sure it completed successfully (green checkmark)
- **Verify Pages source**: Settings → Pages → Source should be "GitHub Actions"

### Workflow failing?

Check the workflow logs for:
- GitBook CLI installation errors
- Missing `book.json` or `SUMMARY.md`
- Node.js version issues
- Permission errors

### Need to manually rebuild?

1. Make a small change to any file in `docs/` folder
2. Commit and push: `git commit -m "Trigger docs rebuild" && git push`
3. Or manually trigger via Actions → Run workflow

