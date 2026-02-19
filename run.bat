@echo off
if not exist "sosubmit\Scripts\python.exe" (
    echo Virtual environment not found. Please run installation first.
    pause
    exit /b
)

start "" "sosubmit\Scripts\pythonw.exe" "main.py"
