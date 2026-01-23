# Changelog

All notable changes to VibeSec will be documented in this file.

## [0.2.0] - 2026-01-23 (Milestone Release)

### Added
- **Scan Cancellation**: Users can now cancel running scans at any stage
  - Proper cleanup of temporary files and resources
  - Fixed database session isolation issues
  - Made SAST scanner non-blocking with async subprocess execution
- **Layman Explanations**: Added user-friendly security explanations for findings
  - Specific explanations for common vulnerabilities (SQL injection, CORS, secrets)
  - Category-based fallback explanations
  - Available for both SAST and SCA findings

### Fixed
- Database enum missing `'cancelled'` status (migration 002)
- Race condition in scan status updates
- Blocking subprocess calls preventing scan cancellation
- Database session isolation preventing cancellation detection

### Changed
- Refactored SAST scanner to use `asyncio.create_subprocess_exec`
- Updated scan execution logic to check cancellation before each phase
- Added `layman_explanation` column to findings table

### Technical Details
- Migration: Added `'cancelled'` to `scanstatus` enum
- Migration: Added `layman_explanation` TEXT column to `findings` table
- Improved database query pattern for cross-session state detection

## [0.1.0] - Initial Release
- Basic SAST and SCA scanning
- Production readiness scoring across 6 domains
- GitHub integration
- Firebase authentication
