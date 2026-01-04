generate-api:
	python ../docs/spec/remove_extra_tags.py sandboxes
	openapi-python-client generate --output-path agentbox/api/api --overwrite --path ../docs/spec/openapi_generated.yml
	rm -rf agentbox/api/client
	mv agentbox/api/api/open_api_client agentbox/api/client
	rm -rf agentbox/api/api

init:
	pip install openapi-python-client datamodel-code-generator==0.34.0

lint:
	ruff check .

generate-mcp:
	datamodel-codegen \
			--input ../docs/spec/mcp-server.json \
			--input-file-type jsonschema \
			--output agentbox/sandbox/mcp.py \
			--output-model-type typing.TypedDict \
			--target-python-version 3.9 \
			--class-name McpServer \
			--use-field-description \
			--disable-timestamp \
			--extra-fields forbid