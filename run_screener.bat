@echo off
echo ===================================================
echo 🚀 DEGIRO ETF Momentum Screener Starten...
echo ===================================================
echo.
echo Stap 1: Nieuwe data ophalen en Momentum scores berekenen...
python momentum_screener.py

echo.
echo Stap 2: HTML Dashboards genereren...
python generate_html.py
python generate_top26.py

echo.
echo Stap 3: Dashboards openen in je browser...
start momentum_screener_dashboard.html
start top26_portfolio.html

echo.
echo ✅ Alles is klaar!
pause
