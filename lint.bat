@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    RePA 2025 - Lint con Autofix
echo ============================================
echo.

:: Colores para Windows
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "RESET=[0m"

:: Verificar argumentos
set "RUN_BACKEND=0"
set "RUN_FRONTEND=0"

if "%1"=="" (
    set "RUN_BACKEND=1"
    set "RUN_FRONTEND=1"
) else if "%1"=="backend" (
    set "RUN_BACKEND=1"
) else if "%1"=="frontend" (
    set "RUN_FRONTEND=1"
) else if "%1"=="all" (
    set "RUN_BACKEND=1"
    set "RUN_FRONTEND=1"
) else (
    echo Uso: lint.bat [backend^|frontend^|all]
    echo   Sin argumentos: ejecuta ambos
    exit /b 1
)

:: ============================================
:: BACKEND - Python con Ruff
:: ============================================
if "%RUN_BACKEND%"=="1" (
    echo %YELLOW%[Backend]%RESET% Ejecutando Ruff linter...
    echo.
    
    cd backend
    
    :: Verificar si ruff está instalado
    python -m ruff --version >nul 2>&1
    if errorlevel 1 (
        echo %YELLOW%Instalando ruff...%RESET%
        pip install ruff
    )
    
    :: Ejecutar ruff check con autofix (usando python -m para evitar problemas de PATH)
    echo Ejecutando: python -m ruff check --fix --unsafe-fixes src/
    python -m ruff check --fix --unsafe-fixes src/
    set BACKEND_CHECK=!errorlevel!
    
    :: Ejecutar ruff format
    echo.
    echo Ejecutando: python -m ruff format src/
    python -m ruff format src/
    set BACKEND_FORMAT=!errorlevel!
    
    cd ..
    
    if !BACKEND_CHECK! EQU 0 if !BACKEND_FORMAT! EQU 0 (
        echo.
        echo %GREEN%[Backend] Lint completado exitosamente%RESET%
    ) else (
        echo.
        echo %RED%[Backend] Lint completado con errores que requieren revision manual%RESET%
    )
    echo.
)

:: ============================================
:: FRONTEND - ESLint
:: ============================================
if "%RUN_FRONTEND%"=="1" (
    echo %YELLOW%[Frontend]%RESET% Ejecutando ESLint...
    echo.
    
    cd frontend
    
    :: Verificar si node_modules existe
    if not exist "node_modules" (
        echo %YELLOW%Instalando dependencias...%RESET%
        npm install
    )
    
    :: Ejecutar eslint con autofix
    echo Ejecutando: npx eslint . --ext js,jsx --fix
    call npx eslint . --ext js,jsx --fix
    if !errorlevel! EQU 0 (
        set FRONTEND_RESULT=0
    ) else (
        set FRONTEND_RESULT=1
    )
    
    cd ..
    
    if !FRONTEND_RESULT! EQU 0 (
        echo.
        echo %GREEN%[Frontend] Lint completado exitosamente%RESET%
    ) else (
        echo.
        echo %RED%[Frontend] Lint completado con errores que requieren revision manual%RESET%
    )
    echo.
)

echo ============================================
echo    Lint finalizado
echo ============================================

endlocal
