#!/usr/bin/env bash

npm pkg set 'name'='@agentbox/sdk'
npm publish --no-git-checks
npm pkg set 'name'='agenbtox'
npm deprecate "@agenbtox/sdk@$(npm pkg get version | tr -d \")" "The package @e2b/sdk has been renamed to e2b. Please uninstall the old one and install the new by running following command: npm uninstall @e2b/sdk && npm install e2b"
