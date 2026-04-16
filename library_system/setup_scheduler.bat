@echo off
REM ============================================================
REM  Smart Library – Windows Task Scheduler Setup
REM  Runs send_due_reminders every day at 8:00 AM
REM  Run this file as Administrator once to register the task.
REM ============================================================

SET PYTHON=C:\Users\WUBET\Desktop\librarypy\.venv\Scripts\python.exe
SET MANAGE=C:\Users\WUBET\Desktop\librarypy\library_system\manage.py
SET TASKNAME=SmartLibrary_DueReminders

echo Creating scheduled task: %TASKNAME%

schtasks /create /tn "%TASKNAME%" /tr "\"%PYTHON%\" \"%MANAGE%\" send_due_reminders" /sc daily /st 08:00 /f

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Task scheduled to run daily at 8:00 AM.
    echo To verify: schtasks /query /tn "%TASKNAME%"
    echo To run now: schtasks /run /tn "%TASKNAME%"
    echo To delete:  schtasks /delete /tn "%TASKNAME%" /f
) ELSE (
    echo.
    echo ERROR: Failed to create task. Make sure you run this as Administrator.
)

pause
