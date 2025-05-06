@echo off
:: Универсальный запускатор Python-приложения
title Парсер вакансий HH.ru
color 0A

:: Определяем пути к Python
setlocal enabledelayedexpansion
set PYTHON_EXE=python.exe
set PIP_EXE=pip.exe

:: Функция для обновления PATH
:RefreshPath
setlocal
set "Key=HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
for /f "tokens=2,*" %%A in ('reg query "%Key%" /v "Path" 2^>nul') do set "SystemPath=%%B"
endlocal & set "NewPath=%SystemPath%"

:: Проверяем Python в PATH
%PYTHON_EXE% --version >nul 2>&1
if !errorlevel! neq 0 (
    :: Проверяем Python в стандартных местах
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%i in ('where python') do set PYTHON_EXE="%%i"
    ) else (
        :: Если Python не найден - скачиваем и устанавливаем
        echo Python не найден. Устанавливаем...
        curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe
        start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
        del python_installer.exe
        
        :: Обновляем PATH в текущей сессии
        call :RefreshPath
        path "%NewPath%"
        
        set PYTHON_EXE=python.exe
        :: Даем системе время на обработку изменений
        timeout /t 5 >nul
    )
)

:: Проверяем pip
%PYTHON_EXE% -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo Устанавливаем pip...
    curl -L -o get-pip.py https://bootstrap.pypa.io/get-pip.py
    %PYTHON_EXE% get-pip.py
    del get-pip.py
)

:: Устанавливаем зависимости
echo Проверяем зависимости...
%PYTHON_EXE% -c "import tkinter, pandas, requests" >nul 2>&1
if !errorlevel! neq 0 (
    echo Устанавливаем необходимые библиотеки...
    %PYTHON_EXE% -m pip install pandas requests
)

:: Создаем виртуальное окружение (опционально)
if not exist "venv" (
    echo Создаем виртуальное окружение...
    %PYTHON_EXE% -m venv venv
    call venv\Scripts\activate.bat
    %PYTHON_EXE% -m pip install pandas requests
)

:: Запускаем приложение
echo Запуск парсера...
start "" /B %PYTHON_EXE% "%~dp0gui_app.py"

pause