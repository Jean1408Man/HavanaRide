@echo off
REM ============================================================
REM build_windows.bat - Genera el ejecutable para Windows
REM Requisito: Python 3.12 de 64 bits instalado en Windows
REM ============================================================

echo.
echo === HAVANA RIDE - Build para Windows ===
echo.

REM Verificar Python 3.12
py -3.12 --version
if errorlevel 1 (
    echo ERROR: No se encontro Python 3.12.
    echo Instala Python 3.12 de 64 bits desde python.org y vuelve a intentar.
    pause
    exit /b 1
)

REM Crear entorno virtual limpio
echo [1/4] Creando entorno virtual...
py -3.12 -m venv .venv_win
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

call .venv_win\Scripts\activate.bat

REM Actualizar herramientas
echo [2/4] Actualizando pip...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo ERROR: No se pudo actualizar pip/setuptools/wheel.
    pause
    exit /b 1
)

REM Instalar dependencias
echo [3/4] Instalando dependencias...
python -m pip install --only-binary=:all: pygame pyinstaller
if errorlevel 1 (
    echo ERROR: No se pudo instalar pygame o pyinstaller.
    echo Revisa que estes usando Python 3.12 de 64 bits.
    pause
    exit /b 1
)

REM Crear ejecutable
echo [4/4] Creando ejecutable...
python -m PyInstaller --onefile --windowed --name "HavanaRide" ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 (
    echo ERROR: Fallo la creacion del ejecutable.
    pause
    exit /b 1
)

echo.
echo Listo!
echo El ejecutable esta en: dist\HavanaRide.exe
echo.
pause