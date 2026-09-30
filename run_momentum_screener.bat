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
python momentum_generate_html.py
python momentum_generate_top30.py
python momentum_generate_positions.py

echo.
echo Stap 3: Dashboards openen in je browser...
start momentum_screener_dashboard.html
start momentum_top30_portfolio.html
start momentum_huidige_posities.html

echo.
echo Klaar!
goto end

:error
echo.
echo FOUT: Het script is mislukt. Controleer de foutmelding hierboven.

:end
pause
