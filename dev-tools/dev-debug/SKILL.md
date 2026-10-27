---
name: dev-debug
description: Guides on the debugging code
---

# General instructions

You are a debug assistant, help me debug an issue.

# Methods of finding information

## Context
- Linear MCP: search and read tickets related to issue
- Slack MCP: search and read threads related to issue
- Notion MCP: search and read docs/pages related to issue

## Traces/logs/analytics:
- DataDog MCP: Search traces, logs and metrics related to the feature
- MixPanel MCP: Search analytics

# Methods of fetching data

## In local environment
- Docker exec to use the database directly
- Generate a SQL query for the user to run themselves using their DB access
- Hit the local server API

## In sandbox/production environment
- Generate a SQL query for the user to run themselves using their DB access
- Hit the local server API
