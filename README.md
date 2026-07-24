# AI Deploy

![CI](https://github.com/bmtyger/EasyD/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://img.shields.io/codecov/c/github/bmtyger/EasyD)
![PyPI](https://img.shields.io/pypi/v/ai-deploy)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

AI-driven infrastructure compiler and deployer.

Free, open source, runs in your environment.

## Install

```bash
pip install -e .
```

## CLI

```bash
ai-deploy run --target aws --env staging
ai-deploy plan --target aws --env staging
ai-deploy validate --target aws
ai-deploy rollback .deploy/manifest.json
```

## Tracking

```bash
# comment on an existing GitHub issue
GITHUB_TOKEN=... ai-deploy run --github-issue 42 --github-repo owner/repo

# auto-create GitHub epic if no issue number is supplied
GITHUB_TOKEN=... ai-deploy run --github-repo owner/repo --create-github-epic "Deploy my-app to staging"
```

## Jira sync

Set these environment variables to mirror deploy events to Jira:

```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="AI"  # optional, defaults to AI
```

Supported events:
- `spec.ready` creates a deploy request issue
- `security.scan.done`, `cost.validate.done`, `terraform.scan.done` create blocker issues when approval is false
- `deploy.done` creates a summary issue and transitions to Done if live

## License

MIT
