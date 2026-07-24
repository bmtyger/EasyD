# Changelog

## [0.1.0] - 2026-07-25

### Added
- Core CLI with `run`, `plan`, `validate`, `rollback` commands
- Requirements analyzer agent (FastAPI, Docker, env var detection)
- Security scanner agent with Terraform-aware checks
- AWS Terraform emitter placeholder
- GitHub tracking via `gh` CLI with HTTP fallback
- Jira notifier plugin with configurable project key
- Environment promotion and rollback manifest writer
- Ops summary writer with cost variance alert
- GitHub epic auto-creation via `--create-github-epic`
- CI workflow with lint, tests, demo run, and type-check
- PyPI publish workflow
- Makefile for local workflows
