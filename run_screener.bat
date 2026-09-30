@echo off
echo ===================================================
echo DEGIRO ETF Momentum Screener Starten...
echo ===================================================
echo.
echo Stap 1: Nieuwe data ophalen en Momentum scores berekenen...
python -u momentum_screener.py
if errorlevel 1 goto error

echo.
echo Stap 2: HTML Dashboards genereren...
python generate_html.py
python generate_top30.py

echo.
echo Stap 3: Dashboards openen in je browser...
start momentum_screener_dashboard.html
start top30_portfolio.html

echo.
echo Klaar!
goto end

:error
echo.
echo FOUT: Het script is mislukt. Controleer de foutmelding hierboven.

:end
pause
