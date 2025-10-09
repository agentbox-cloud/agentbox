#!/bin/bash

rm -rf agentbox/envd/__pycache__
rm -rf agentbox/envd/filesystem/__pycache__
rm -rf agentbox/envd/process/__pycache__

sed -i.bak 's/from\ process\ import/from agentbox.envd.process import/g' agentbox/envd/process/* agentbox/envd/filesystem/*
sed -i.bak 's/from\ filesystem\ import/from agentbox.envd.filesystem_agentbox import/g' agentbox/envd/process/* agentbox/envd/filesystem/*

rm -f agentbox/envd/process/*.bak
rm -f agentbox/envd/filesystem/*.bak
