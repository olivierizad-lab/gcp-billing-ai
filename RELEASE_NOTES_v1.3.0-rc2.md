# Release v1.3.0-rc2

Release Candidate 2: Auto-discovery of agents and table formatting fixes

## Added

- Agent auto-discovery functionality
- Custom IAM role with Vertex AI reasoning engine permissions
- Mermaid architecture diagrams
- Documentation structure with SUMMARY.md and book.json

## Changed

- Renamed deployment scripts (removed "IAP" and "simple" references)
- Updated authentication documentation to focus on Firestore auth

## Fixed

- Agent Engine auto-discovery IAM permissions
- Service account role bindings

## Key Features

- Automatic agent discovery from Vertex AI Agent Engine
- Fixed-width table formatting for query results
- Improved script naming (removed IAP references)
- History cleanup utilities
- Enhanced error handling and logging

## Breaking Changes

None - backward compatible with fallback to env vars
