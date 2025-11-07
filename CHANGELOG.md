# Changelog

All notable changes to the GCP Billing Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**See also:** [GitHub Releases](https://github.com/olivierizad-lab/gcp-billing-ai/releases)

## [Unreleased]

_No unreleased changes yet._

## [1.5.0] - 2025-11-07

### Added
- Cloud Run metrics collector job with GitHub PAT support and Firestore snapshot storage.
- `/metrics/refresh` API endpoint plus frontend polling flow for on-demand refreshes.
- Makefile targets (`deploy-metrics-job`, `run-metrics-job`) to manage the collector.
- Metrics documentation updates describing the snapshot pipeline and secret configuration.

### Changed
- Metrics dashboard now loads cached snapshots, shows progress feedback, and supports manual refresh.
- Backend automatically injects metrics job configuration during deployment.
- Documentation landing pages updated to version `v1.5.0` with current timestamps.

### Fixed
- Metrics fetch failures stemming from missing auth headers and unconfigured job name.
- Cloud Run job now clones full git history ensuring non-zero commit/LOC totals.
- Metrics UI scrollability issues on smaller viewports.

## [1.4.0-rc3] - 2025-01-27

### Added
- GitHub Pages documentation deployment using Jekyll.
- Custom favicon set (SVG + PNG variants) and Open Graph assets for link previews.
- Documentation Quick Access links and custom CSS for improved formatting.

### Changed
- Updated help modal to match the Provisioner app style with tabbed layout.
- Enhanced documentation structure after migrating away from GitBook CLI.
- Deployment scripts cleaned up (removed IAP references, clarified Firestore auth).

### Fixed
- Table formatting in the chat UI (fixed-width tables).
- Agent loading regressions related to IAM and auto-discovery fallbacks.
- Documentation index/headers rendering issues and stale files.
- Link previews in messaging apps using the new favicon/OG tags.

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
