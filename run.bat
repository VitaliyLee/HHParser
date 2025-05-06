@echo off
title The Job Parser HH.ru
color 0A

:: Проверяем установлен ли Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or added to the PATH
    pause
    exit /b
)

:: Проверяем установлены ли необходимые библиотеки
python -c "import tkinter, pandas, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing the necessary libraries...
    pip install pandas requests
)

:: Запускаем парсер
echo Launching a job parser HH.ru ...
python "%~dp0gui_app.py"

pause