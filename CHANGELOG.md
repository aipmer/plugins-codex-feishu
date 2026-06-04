# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, adjusted for this repository's release-note style.

## [0.3.2] - 2026-06-04

### Added

- Lightweight daily digest entry: `npm run feishu -- digest --preview` and `npm run feishu -- digest --send --confirm`.
- Repo-provided digest wrapper script for reusing the existing Feishu project update push flow.
- Docs-level macOS `launchd` example for personal scheduled digest sending.
- `/ids` command and richer `/status` output for faster Feishu bot diagnostics.

### Changed

- Default Feishu digest flow now prefers Chinese titles and Chinese section labels.
- Default digest template is fully localized to Chinese for real private assistant push scenarios.
- README and README.zh-CN now document the lightweight digest path instead of a built-in schedule subsystem.

### Fixed

- Resolved real-world event delivery confusion caused by using the wrong Feishu `App ID` during bot validation.
- Added duplicate `message_id` protection to avoid repeated replies when Feishu retries the same event.
- Clarified local service and runtime verification paths so `launchd` status, bot bridge status, and push verification are easier to distinguish.

## [0.3.0-beta] - 2026-06-04

- Introduced the Feishu bot bridge, queueing, access control, `launchd` service management, and local verification flow.
- See [docs/releases/v0.3.0-beta.md](./docs/releases/v0.3.0-beta.md).

## [0.1.1] - 2026-05-24

- Added webhook server, smoke tests, private assistant push guidance, and release-prep tooling.
- See [docs/releases/v0.1.1.md](./docs/releases/v0.1.1.md).
