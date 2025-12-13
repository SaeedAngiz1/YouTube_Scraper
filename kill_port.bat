@echo off
echo Checking for processes using port 8501...
echo.

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8501') do (
    echo Found process using port 8501: PID %%a
    echo Killing process...
    taskkill /PID %%a /F
    echo Process killed!
    goto :done
)

echo Port 8501 is free!
:done
echo.
echo You can now run: streamlit run app.py
pause

