# Changelog

All notable changes to the GCP Billing Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**See also:** [GitHub Releases](https://github.com/olivierizad-lab/gcp-billing-ai/releases)

## [Unreleased]

### Added
- GitHub Pages documentation deployment using Jekyll
- Custom favicon with dollar sign and cloud theme (SVG and PNG versions)
- PNG favicon versions (1200x1200, 512x512, 180x180) for better messaging app compatibility
- Open Graph meta tags for rich link previews in messaging apps (Apple Messages, WhatsApp, etc.)
- Favicon conversion script using Sharp library
- Documentation Quick Access links (now clickable)
- Custom CSS for improved documentation formatting and styling
- nginx sub_filter configuration to inject absolute URLs for OG images
- Cloud Run metrics collector job (GitHub PAT + Firestore snapshots) and `/metrics/refresh` endpoint

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

## [1.3.0-rc2] - 2025-01-XX

### Added
- Agent auto-discovery functionality
- Custom IAM role with Vertex AI reasoning engine permissions
- Mermaid architecture diagrams
- Documentation structure with SUMMARY.md and book.json

### Changed
- Renamed deployment scripts (removed "IAP" and "simple" references)
- Updated authentication documentation to focus on Firestore auth

### Fixed
- Agent Engine auto-discovery IAM permissions
- Service account role bindings

## [1.3.0] - 2025-01-XX

### Added
- Web interface for interacting with agents
- Firestore-based authentication with domain restrictions
- Real-time streaming responses
- Query history management
- Multi-agent support
- Auto-discovery of deployed reasoning engines
- Comprehensive documentation

### Changed
- Migrated from IAP to Firestore authentication
- Simplified deployment process

## [1.2.0] - 2025-01-XX

### Added
- BigQuery agent implementation
- Vertex AI Agent Engine integration
- Cloud Run deployment
- FastAPI backend

## [1.1.0] - 2025-01-XX

### Added
- Initial project structure
- Agent Development Kit (ADK) integration
- Basic query processing

## [1.0.0] - 2025-01-XX

### Added
- Initial release
- Project setup and configuration
