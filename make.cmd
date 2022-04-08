@echo off
CALL version.cmd

echo [MAKE] Creating build folders
if not exist ".\build" mkdir .\build
if not exist ".\build\pdf" mkdir .\build\pdf

echo [MAKE] Copy files to build folder
xcopy .\mscz .\build\mscz\ /s /e > nul
echo F | xcopy .\cover.rtf .\build\cover.rtf > nul

echo [MAKE] Exporting PDFs from MSCZs
FOR /F "tokens=*" %%G IN ('dir /b .\build\mscz\*.mscz') DO MuseScore3 ".\build\mscz\%%G" -o ".\build\pdf\%%~nG.pdf"

echo [MAKE] Creating Cover PDF
powershell .\AddContents.ps1
"%ProgramFiles%\Windows NT\Accessories\WORDPAD.EXE" /pt ".\build\cover.rtf" "Microsoft Print to PDF" "Microsoft Print to PDF" ".\build\pdf\00_cover.pdf"

echo [MAKE] Merging PDFs
pdftk .\build\pdf\*.pdf cat output JsRealBook_%__version__%.pdf

echo [MAKE] Remove Build Folder
rd /s /q .\build
