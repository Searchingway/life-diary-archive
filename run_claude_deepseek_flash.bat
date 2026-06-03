@echo off
chcp 65001

set ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
set ANTHROPIC_AUTH_TOKEN=sk-bc8cde6da86041999df5d0015dbc68f1

set ANTHROPIC_MODEL=deepseek-v4-flash[1m]
set ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-flash[1m]
set ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-flash[1m]
set ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash[1m]
set CLAUDE_CODE_SUBAGENT_MODEL=deepseek-v4-flash[1m]
set CLAUDE_CODE_EFFORT_LEVEL=high

@REM 设置1M上下文
set ANTHROPIC_MAX_TOKENS=1000000

cd /d "%~dp0"
claude --permission-mode bypassPermissions

pause