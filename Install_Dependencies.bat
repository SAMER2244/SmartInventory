@echo off
chcp 65001 >nul 2>&1
title SmartInventory - Kurulum Asistani
color 0A

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     SMARTINVENTORY ENVANTER YONETIM SISTEMI         ║
echo  ║          Kurulum Asistani v3.0               ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM ── Step 1: Check Python ──────────────────────────────────────────────
echo [1/5] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [HATA] Python bulunamadi!
    echo  Lutfen https://www.python.org/downloads/ adresinden yukleyin.
    echo  Kurulum sirasinda "Add Python to PATH" secenegini isaretleyin.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo   Bulundu: %%i
echo.

REM ── Step 2: Create Virtual Environment ────────────────────────────────
echo [2/5] Sanal ortam olusturuluyor (.venv)...
if exist ".venv\Scripts\python.exe" (
    echo   .venv zaten mevcut, atlaniyor.
) else (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo  [HATA] Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
    echo   .venv basariyla olusturuldu.
)
echo.

REM ── Step 3: Install Dependencies ──────────────────────────────────────
echo [3/5] Bagimliliklar yukleniyor (requirements.txt)...
echo   pip guncelleniyor...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
echo   Paketler yukleniyor...
.venv\Scripts\pip.exe install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [HATA] Paket yuklemesi basarisiz!
    echo  Lutfen internet baglantinizi kontrol edin.
    pause
    exit /b 1
)
echo   Tum bagimliliklar basariyla yuklendi.
echo.

REM ── Step 4: Create Directories ────────────────────────────────────────
echo [4/5] Proje klasorleri kontrol ediliyor...
if not exist "data" (
    mkdir data
    echo   data\ klasoru olusturuldu.
) else (
    echo   data\ zaten mevcut.
)
if not exist "logs" (
    mkdir logs
    echo   logs\ klasoru olusturuldu.
) else (
    echo   logs\ zaten mevcut.
)
if not exist "outputs" (
    mkdir outputs
    echo   outputs\ klasoru olusturuldu.
) else (
    echo   outputs\ zaten mevcut.
)
echo.

REM ── Step 5: Create .env Template ──────────────────────────────────────
echo [5/5] Ortam degiskenleri dosyasi (.env) kontrol ediliyor...
if not exist ".env" (
    (
        echo # SmartInventory API Anahtarlari
        echo # Bu degerleri kendi anahtarlarinizla degistirin
        echo GROQ_API_KEY=
        echo GEMINI_API_KEY=
    ) > .env
    echo   .env sablonu olusturuldu.
    echo   [ONEMLI] Lutfen .env dosyasini acip API anahtarlarinizi girin.
) else (
    echo   .env zaten mevcut.
)
echo.

REM ── Done ──────────────────────────────────────────────────────────────
echo  ╔══════════════════════════════════════════════╗
echo  ║       KURULUM BASARIYLA TAMAMLANDI!          ║
echo  ║                                              ║
echo  ║  Uygulamayi baslatmak icin:                  ║
echo  ║  Start_App.bat dosyasini calistirin.     ║
echo  ╚══════════════════════════════════════════════╝
echo.
pause
