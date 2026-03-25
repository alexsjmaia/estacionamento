@echo off
cd /d %~dp0

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe local_print_agent.py
) else (
    python local_print_agent.py
)

pause
