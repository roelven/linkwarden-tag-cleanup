# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-20

### Added
- Initial release of Linkwarden Tag Cleanup Tools
- Tag analysis script to identify duplicates and overlaps
- Tag consolidation script to merge and clean up tags
- Tag normalization service for ongoing tag quality
- Junk tag removal script with 200+ built-in patterns
- Comprehensive documentation and guides
- Wrapper scripts for easy execution
- Systemd integration for automated normalization
- Custom blocklist support for junk tags
- Dry-run mode for all operations
- Automatic backup before changes

### Features
- Case-insensitive duplicate detection
- Semantic overlap identification
- Fuzzy tag matching (configurable threshold)
- Automatic case normalization (Title Case + acronyms)
- Configurable usage thresholds
- Rate limiting to avoid API throttling
- Error handling and recovery
- Progress tracking and statistics

### Documentation
- Quick start guide
- Junk tags removal guide
- Comprehensive testing guide
- Implementation summary
- Deployment instructions for systemd
- Contributing guidelines

## [Unreleased]

### Planned
- Web UI for configuration and management
- Additional LLM integrations
- Tag analytics dashboard
- Docker containerization
- CI/CD pipeline
- Integration tests
