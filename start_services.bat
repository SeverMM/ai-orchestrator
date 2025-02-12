@echo off
setlocal

REM Define the project root directory
set "PROJECT_ROOT=C:\ai-orchestrator"

REM Set PYTHONPATH to the project root so that Python can find all modules
set "PYTHONPATH=%PROJECT_ROOT%"

echo Starting Atlas...
start "Atlas" cmd /k python "%PROJECT_ROOT%\services\atlas\service.py"

echo Starting Nova...
start "Nova" cmd /k python "%PROJECT_ROOT%\services\nova\service.py"

echo Starting Sage...
start "Sage" cmd /k python "%PROJECT_ROOT%\services\sage\service.py"

echo Starting Echo...
start "Echo" cmd /k python "%PROJECT_ROOT%\services\echo\service.py"

echo Starting Pixel...
start "Pixel" cmd /k python "%PROJECT_ROOT%\services\pixel\service.py"

echo Starting Quantum...
start "Quantum" cmd /k python "%PROJECT_ROOT%\services\quantum\service.py"

echo All services started. Press any key to exit.
pause
