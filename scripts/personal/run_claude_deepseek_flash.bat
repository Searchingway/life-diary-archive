@echo off
chcp 65001

set ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
set ANTHROPIC_AUTH_TOKEN=sk-889a0dd1327240768b6cd389ab77b447

set ANTHROPIC_MODEL=deepseek-v4-flash
set ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-flash
set ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-flash
set ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash
set CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash
set CLAUDE_CODE_EFFORT_LEVEL=high

cd /d "%~dp0"
claude

pause