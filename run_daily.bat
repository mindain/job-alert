@echo off
cd /d C:\Users\darwi\Projects\sesac-lab\job-alert
call ..\.venv\Scripts\activate.bat
python run_all.py >> logs\run_%date:~0,4%-%date:~5,2%-%date:~8,2%.txt 2>&1
if errorlevel 1 python send_mail.py --fail >> logs\run_%date:~0,4%-%date:~5,2%-%date:~8,2%.txt 2>&1
