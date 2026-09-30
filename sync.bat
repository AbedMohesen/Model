@echo off
chcp 65001 > nul
echo ========================================================
echo Starting IUG Moodle Automated Synchronization...
echo ========================================================
python moodle_sync.py
echo.
pause
