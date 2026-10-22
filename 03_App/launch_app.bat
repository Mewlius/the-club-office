@echo off
rem The Club Office - start the app
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Premiere utilisation : preparation, une ou deux minutes...
    py -3 -m venv .venv 2>nul || python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo L'installation a echoue. Verifie ta connexion internet, puis relance ce fichier.
    pause
    exit /b 1
)

echo.
echo The Club Office s'ouvre dans ton navigateur. Ferme cette fenetre pour arreter l'app.
python main.py
pause
