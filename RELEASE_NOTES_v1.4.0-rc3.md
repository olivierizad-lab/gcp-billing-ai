# Release v1.4.0-rc3

**Release Candidate 3: Favicon, Open Graph tags, and documentation improvements**

## Key Features

- **Custom favicon** with dollar sign and cloud theme (SVG and PNG versions)
- **Open Graph meta tags** for rich link previews in messaging apps
- **PNG favicon versions** for better compatibility (1200x1200, 512x512, 180x180)
- **Documentation improvements** (Jekyll, formatting, Quick Access links)
- **nginx configuration** for absolute URL injection
- **Improved build configuration**

## Changes since v1.3.0-rc2

### Added
- GitHub Pages documentation deployment using Jekyll
- Custom favicon with dollar sign and cloud theme (SVG and PNG versions)
- PNG favicon versions (1200x1200, 512x512, 180x180) for better messaging app compatibility
- Open Graph meta tags for rich link previews in messaging apps (Apple Messages, WhatsApp, etc.)
- Favicon conversion script using Sharp library
- Documentation Quick Access links (now clickable)
- Custom CSS for improved documentation formatting and styling
- nginx sub_filter configuration to inject absolute URLs for OG images

### Changed
- Switched documentation from GitBook CLI to Jekyll for GitHub Pages
- Updated help menu to match provisioner app style with tabbed modal
- Improved favicon visibility (larger dollar sign, solid background)
- Enhanced documentation formatting (tables, lists, spacing)
- Updated deployment scripts to remove IAP references (now uses Firestore authentication)
- Improved nginx configuration for better OG image URL handling

### Fixed
- Table formatting in UI (fixed-width columns)
- Agent loading issues (IAM permissions and fallback mechanism)
- Documentation build and deployment issues
- Documentation header formatting (removed unformatted text)
- Removed obsolete documentation files
- Quick Access links in documentation (now functional)
- Link previews in messaging apps (Apple Messages, etc.)

## Installation

See [Getting Started Guide](https://olivierizad-lab.github.io/gcp-billing-ai/START_HERE.html) for deployment instructions.

## Documentation

Full documentation available at: https://olivierizad-lab.github.io/gcp-billing-ai/

