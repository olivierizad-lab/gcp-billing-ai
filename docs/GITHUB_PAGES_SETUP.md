# GitHub Pages Setup Instructions

## Issue: Documentation Index Not Loading

If your GitHub Pages site is showing the root README.md instead of the GitBook-built documentation, follow these steps:

## 1. Configure GitHub Pages to Use GitHub Actions

1. Go to your repository on GitHub: `https://github.com/olivierizad-lab/gcp-billing-ai`
2. Click **Settings** → **Pages**
3. Under **Source**, select **GitHub Actions** (not "Deploy from a branch")
4. Save the changes

## 2. Verify the Workflow Has Run

1. Go to the **Actions** tab in your repository
2. Look for the "Build and Deploy Documentation" workflow
3. Ensure it has run and completed successfully
4. If it failed, check the logs for errors

## 3. Wait for Deployment

After the workflow completes successfully, it may take 1-2 minutes for GitHub Pages to update.

## 4. Verify the Site

Visit: `https://olivierizad-lab.github.io/gcp-billing-ai/`

You should see:
- The Documentation Index page (not the root README)
- Navigation sidebar with all documentation sections
- GitBook-styled documentation

## Manual Workflow Trigger

If the workflow hasn't run automatically:

1. Go to **Actions** → **Build and Deploy Documentation**
2. Click **Run workflow** → **Run workflow**

## Troubleshooting

### Still seeing README.md?
- Check that GitHub Pages source is set to "GitHub Actions"
- Verify the workflow completed successfully
- Wait 2-3 minutes after workflow completion
- Clear your browser cache

### Workflow failing?
- Check that `docs/book.json` and `docs/SUMMARY.md` exist
- Verify GitBook CLI can be installed (npm)
- Check workflow logs for specific errors

