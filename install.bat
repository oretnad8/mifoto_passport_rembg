@echo off
echo ===============================================
echo   Mi Foto Carnet - Instalador de Dependencias
echo ===============================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor, instala Python 3.8 o superior desde https://python.org
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Actualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Hubo un problema instalando las dependencias
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   Instalacion completada exitosamente!
echo ===============================================
echo.
echo Para ejecutar la aplicacion:
echo   python main.py
echo.
pause