# Changelog

All notable changes to the GCP Billing Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**See also:** [GitHub Releases](https://github.com/olivierizad-lab/gcp-billing-ai/releases)

## [Unreleased]

### Added
- GitHub Pages documentation deployment using Jekyll
- Metrics page infrastructure (backend endpoint and frontend components)
- Help modal with tabbed interface (About, Help, Documentation, Implementation)
- Agent auto-discovery from Vertex AI Agent Engine
- Fallback mechanism for agent configuration via environment variables

### Changed
- Switched documentation from GitBook CLI to Jekyll for GitHub Pages
- Updated help menu to match provisioner app style with tabbed modal
- Removed local development instructions from documentation
- Updated deployment scripts to remove IAP references (now uses Firestore authentication)

### Fixed
- Table formatting in UI (fixed-width columns)
- Agent loading issues (IAM permissions and fallback mechanism)
- Documentation build and deployment issues
- Removed obsolete documentation files

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
