@echo off
echo ===================================================
echo 🚀 DEGIRO ETF Momentum Screener Starten...
echo ===================================================
echo.
echo Stap 1: Nieuwe data ophalen en Momentum scores berekenen...
python momentum_screener.py

echo.
echo Stap 2: HTML Dashboard genereren...
python generate_html.py

echo.
echo Stap 3: Dashboard openen in je browser...
start momentum_screener_dashboard.html

echo.
echo ✅ Alles is klaar!
pause
