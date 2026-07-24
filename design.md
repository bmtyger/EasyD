# ai-deploy design

## Goals
- Free open-source deploy compiler/runtime.
- Runs in user's environment or GitHub Actions.
- Cloud-agnostic core with provider plugins.
- Tracking via GitHub-native issue/PR artifacts; optional Jira sync.

## Non-goals (v0)
- Managed hosting of deploys.
- Multi-tenant control plane.

## Components
- CLI: parse args, run headless/interactive.
- EventBus: in-process pub/sub.
- Agents: requirements, architect, security, provisioner, validator, ops.
- Plugins: providers, detectors, scanners, notifiers.
- Tracking: GitHub Issues/PR comments by default; optional Jira sync.
- State: repo-local `.deploy/` manifests.

## Data model
- AppSpec, DeploymentPackage, DeployState in `core/types.py`.

## Plugin contract
- Directory with `plugin.json` manifest.
- Supported interface keys: detect, emit, plan, rollback, notify.

## Workflow
- `ai-deploy run --target aws --env staging`
- requirements -> spec
- approval gate if non-standard
- security scan
- cost estimate
- architect emits DeploymentPackage
- provisioner applies by dependency order
- validator posts result
- state serialized to `.deploy/state.json`

## Install
- `pip install ai-deploy`
- Docker: `ghcr.io/...`
- Build: `pip install build && python -m build`
