@echo off
echo ===================================================
echo DEGIRO ETF Fundamentals Screener Starten...
echo ===================================================

echo.
echo Stap 1: Nieuwe data ophalen en Risico scores berekenen...
python fundamentals_screener.py

echo.
echo Stap 2: HTML Dashboard genereren...
python fundamentals_generate_html.py

echo.
echo Stap 3: Top 30 Dashboard genereren...
python fundamentals_generate_top30.py

echo.
echo Stap 4: Dashboards openen in je browser...
start fundamentals_screener_dashboard.html
start fundamentals_top30_portfolio.html

echo.
echo Klaar!
pause
