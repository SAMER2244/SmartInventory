@echo off
chcp 65001 >nul 2>&1
title SmartInventory - Envanter Yonetim Sistemi
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║     SMARTINVENTORY ENVANTER YONETIM SISTEMI         ║
echo  ║            Baslatiliyor...                   ║
echo  ╚══════════════════════════════════════════════╝
echo.

REM ── Check .env exists ────────────────────────────────────────────────
if not exist ".env" (
    echo GROQ_API_KEY= > .env
    echo GEMINI_API_KEY= >> .env
    echo  [INFO] .env file automatically created.
    echo.
)

REM ── Check .venv exists ────────────────────────────────────────────────
if not exist ".venv\Scripts\activate.bat" (
    echo  [HATA] Sanal ortam bulunamadi!
    echo  Lutfen once Install_Dependencies.bat dosyasini calistirin.
    echo.
    pause
    exit /b 1
)

REM ── Activate Virtual Environment ──────────────────────────────────────
echo [1/2] Sanal ortam aktif ediliyor...
call .venv\Scripts\activate.bat
echo   Ortam aktif.
echo.

REM ── Launch Streamlit ──────────────────────────────────────────────────
echo [2/2] Streamlit sunucusu baslatiliyor...
echo   Tarayici otomatik olarak acilacak...
echo   Kapatmak icin bu pencereyi kapatin veya CTRL+C basin.
echo.
echo  ──────────────────────────────────────────────
echo   Yerel Adres:  http://localhost:8501
echo  ──────────────────────────────────────────────
echo.

REM Open browser after a short delay
start "" http://localhost:8501

REM Start Streamlit with dark theme
streamlit run app.py --server.headless true --theme.base "dark"

REM If Streamlit exits, keep window open
echo.
echo  Sunucu durduruldu.
pause
