# GCP Billing Agent Documentation

Welcome to the GCP Billing Agent documentation. This documentation is automatically built and deployed to GitHub Pages.

## Documentation Structure

This documentation is organized into the following sections:

- **Getting Started** - Quick start guides and architecture overview
- **Deployment** - Deployment guides and automation
- **Authentication & Security** - Security setup and best practices
- **Agents** - Agent-specific documentation
- **Solution Documentation** - Gen AI solution details
- **Testing** - Testing guides and documentation

## Building Locally

To build and preview the documentation locally:

```bash
# Install GitBook CLI
npm install -g gitbook-cli

# Install plugins
cd docs
gitbook install

# Build documentation
gitbook build

# Serve locally
gitbook serve
```

Then open http://localhost:4000 in your browser.

## Automatic Deployment

This documentation is automatically built and deployed to GitHub Pages whenever changes are pushed to the `main` branch in the `docs/` folder.

The documentation is available at: https://olivierizad-lab.github.io/gcp-billing-ai
