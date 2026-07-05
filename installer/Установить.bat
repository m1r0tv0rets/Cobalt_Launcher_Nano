@echo off
chcp 1251 > nul
cls

echo ===================================================
echo   Установка лаунчера Cobalt Nano
echo ===================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo [ОШИБКА] Скрипт запущен без прав администратора!
    echo.
    echo Чтобы файлы смогли скопироваться на диск C:\, пожалуйста:
    echo Нажмите на этот файл ПРАВОЙ кнопкой мыши и выберите:
    echo --^> "Запуск от имени администратора"
    echo.
    pause
    exit /B
)

cd /d "%~dp0"

set "ROOT=C:\cobalt_launcher_nano_reliz"
set "MODELS=%ROOT%\launcher_models"

echo [1/4] Создание системных папок...
if not exist "%ROOT%" mkdir "%ROOT%"
if not exist "%MODELS%" mkdir "%MODELS%"

echo [2/4] Поиск исполняемого файла лаунчера...
set "EXE="
for %%F in (*.exe) do (
    if /I not "%%~fF"=="%~f0" set "EXE=%%~fF"
)

if not defined EXE (
    color 0C
    echo [ОШИБКА] Файл лаунчера .exe не найден в текущей папке!
    echo Убедитесь, что распаковали архив перед запуском.
    echo.
    pause
    exit
)

echo [3/4] Копирование ядра лаунчера (KERNEL.exe)...
copy /Y "%EXE%" "%ROOT%\KERNEL.exe" > nul

echo [4/4] Копирование компонентов моделей...
if exist "install_launcher_models" (
    xcopy "install_launcher_models\*.*" "%MODELS%\" /E /I /Y > nul
) else (
    echo [ПРЕДУПРЕЖДЕНИЕ] Папка install_launcher_models не найдена рядом с батником!
)

set "DESKTOP_DIR=%PUBLIC%\Desktop"
if not exist "%DESKTOP_DIR%" set "DESKTOP_DIR=%USERPROFILE%\Desktop"

set "VBS=%TEMP%\cobalt_shortcut.vbs"
echo Set W = CreateObject("WScript.Shell") > "%VBS%"
echo Set L = W.CreateShortcut("%DESKTOP_DIR%\Cobalt Nano Launcher.lnk") >> "%VBS%"
echo L.TargetPath = "%ROOT%\KERNEL.exe" >> "%VBS%"
echo L.WorkingDirectory = "%ROOT%" >> "%VBS%"
echo L.Save >> "%VBS%"

cscript /nologo "%VBS%" > nul
del "%VBS%"

echo.
color 0A
echo ===================================================
echo   Установка Cobalt Launcher Nano успешно завершена!
echo   Ярлык добавлен на ваш Рабочий стол.
echo ===================================================
echo.
pause