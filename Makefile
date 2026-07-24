.PHONY: install test lint run plan validate rollback clean

install:
	pip install -e .

test:
	pytest -q

lint:
	pip install mypy
	mypy ai_deploy

run:
	ai-deploy run --target aws --env staging --repo demo-fastapi/app --output .deploy/package.json --state-file .deploy/state.json

plan:
	ai-deploy plan --repo demo-fastapi/app --output .deploy/plan.json

validate:
	ai-deploy validate --repo demo-fastapi/app --output .deploy/validation.json

rollback:
	ai-deploy rollback .deploy/manifest.json --output .deploy/rollback-restore.json

clean:
	rm -rf .deploy .pytest_cache dist build *.egg-info
