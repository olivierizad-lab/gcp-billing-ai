# GitBook Setup Guide

This guide explains how to set up and publish the GitBook documentation for the GCP Billing Agent project.

## GitBook Structure

The documentation is organized in the `docs/` directory with:
- `SUMMARY.md` - Table of contents for GitBook
- `book.json` - GitBook configuration
- Individual markdown files for each documentation section

## Publishing to GitBook

### Option 1: GitBook.com (Recommended)

1. **Create a GitBook account**
   - Go to https://www.gitbook.com
   - Sign up or sign in

2. **Create a new space**
   - Click "New" → "Space"
   - Choose "Import from GitHub" (recommended) or "Create blank space"
   - If importing from GitHub:
     - Select your repository: `olivierizad-lab/gcp-billing-ai`
     - Select root path: `docs/`
     - GitBook will automatically detect `SUMMARY.md` and `book.json`

3. **Configure GitBook**
   - GitBook will use `book.json` for configuration
   - Update the GitBook URL in `web/frontend/src/App.jsx`:
     ```javascript
     const GITBOOK_BASE_URL = 'https://your-org.gitbook.io/gcp-billing-agent'
     ```

4. **Publish**
   - GitBook automatically builds when you push to GitHub
   - Or manually trigger builds in GitBook settings

### Option 2: GitHub Pages

1. **Install GitBook CLI**
   ```bash
   npm install -g gitbook-cli
   ```

2. **Install plugins**
   ```bash
   cd docs
   gitbook install
   ```

3. **Build GitBook**
   ```bash
   gitbook build
   ```
   This creates a `_book/` directory with HTML files.

4. **Deploy to GitHub Pages**
   - Use GitHub Actions to automatically build and deploy
   - Or manually push `_book/` contents to `gh-pages` branch

### Option 3: Local Development

1. **Install GitBook CLI**
   ```bash
   npm install -g gitbook-cli
   ```

2. **Serve locally**
   ```bash
   cd docs
   gitbook serve
   ```
   Open http://localhost:4000

## Updating Documentation Links in Frontend

After publishing GitBook, update the GitBook URL in the frontend:

**File**: `web/frontend/src/App.jsx`

```javascript
// Update this to your actual GitBook URL
const GITBOOK_BASE_URL = 'https://your-org.gitbook.io/gcp-billing-agent'
```

Or set it as an environment variable:

```javascript
const GITBOOK_BASE_URL = import.meta.env.VITE_GITBOOK_URL || 'https://your-org.gitbook.io/gcp-billing-agent'
```

Then add to your build configuration:
```bash
VITE_GITBOOK_URL=https://your-org.gitbook.io/gcp-billing-agent
```

## Documentation Structure

The documentation is organized in `SUMMARY.md`:

```
Getting Started
├── Start Here
├── Getting Started
└── Architecture

Deployment
├── Automated Deployment
├── Cloud Run Deployment
├── Deployment Overview
├── Backend Deployment
├── Frontend Deployment
└── Deployment FAQ

Authentication & Security
├── Authentication Setup
└── Security

Agents
├── Agent Overview
├── bq_agent_mick
├── bq_agent
└── ... more agent docs

Solution Documentation
└── Gen AI Solution

Testing
├── Testing History
└── Test Documentation
```

## Adding New Documentation

1. Create a new markdown file in the appropriate directory
2. Add the entry to `SUMMARY.md` in the correct section
3. Push to GitHub (GitBook will auto-update if connected)

## Troubleshooting

### GitBook not detecting SUMMARY.md
- Ensure `SUMMARY.md` is in the root of the `docs/` directory
- Check that the file is committed to GitHub

### Links not working
- Use relative paths in markdown files: `[Link Text](./filename.md)`
- GitBook will automatically convert these to proper links

### Mermaid diagrams not rendering
- Install the `mermaid-gb3` plugin (already in `book.json`)
- Or use GitBook's built-in diagram support

## References

- [GitBook Documentation](https://docs.gitbook.com/)
- [GitBook GitHub Integration](https://docs.gitbook.com/integrations/github)
- [GitBook CLI](https://github.com/GitbookIO/gitbook)

