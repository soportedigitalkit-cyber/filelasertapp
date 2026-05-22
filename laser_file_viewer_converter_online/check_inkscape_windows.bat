@echo off
echo Revisando si Inkscape esta disponible...
where inkscape >nul 2>nul
if %errorlevel%==0 (
  echo Inkscape detectado en PATH:
  where inkscape
  pause
  exit /b 0
)
where inkscape.com >nul 2>nul
if %errorlevel%==0 (
  echo Inkscape detectado en PATH:
  where inkscape.com
  pause
  exit /b 0
)
if exist "C:\Program Files\Inkscape\bin\inkscape.com" (
  echo Inkscape detectado en C:\Program Files\Inkscape\bin\inkscape.com
  pause
  exit /b 0
)
if exist "C:\Program Files\Inkscape\bin\inkscape.exe" (
  echo Inkscape detectado en C:\Program Files\Inkscape\bin\inkscape.exe
  pause
  exit /b 0
)
echo Inkscape no fue detectado. La app igual funciona para previews y conversiones simples.
echo Para instalarlo, descarga Inkscape desde el sitio oficial y reinicia VSCode/terminal.
pause
