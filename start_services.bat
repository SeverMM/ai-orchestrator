@echo off
setlocal

echo Starting Atlas...
start "Atlas" cmd /k python "C:\ai-orchestrator\services\atlas\service.py"

echo Starting Nova...
start "Nova" cmd /k python "C:\ai-orchestrator\services\nova\service.py"

echo Starting Sage...
start "Sage" cmd /k python "C:\ai-orchestrator\services\sage\service.py"

echo Starting Echo...
start "Echo" cmd /k python "C:\ai-orchestrator\services\echo\service.py"

echo Starting Pixel...
start "Pixel" cmd /k python "C:\ai-orchestrator\services\pixel\service.py"

echo Starting Quantum...
start "Quantum" cmd /k python "C:\ai-orchestrator\services\quantum\service.py"

echo All services started. Press any key to exit.
pause
