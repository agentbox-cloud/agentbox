generate-api:
	python ../docs/spec/remove_extra_tags.py sandboxes
	openapi-python-client generate --output-path agentbox/api/api --overwrite --path ../docs/spec/openapi_generated.yml
	rm -rf agentbox/api/client
	mv agentbox/api/api/open_api_client agentbox/api/client
	rm -rf agentbox/api/api

init:
	pip install openapi-python-client

lint:
	ruff check .
