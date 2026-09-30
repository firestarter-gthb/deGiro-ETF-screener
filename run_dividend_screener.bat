@echo off
echo ===================================================
echo DEGIRO ETF Dividend Screener Starten...
echo ===================================================
echo.
echo Stap 1: Nieuwe data ophalen en Dividend yields berekenen...
python -u dividend_screener.py
if errorlevel 1 goto error

echo.
echo Stap 2: HTML Dashboard genereren...
python dividend_generate_html.py
python dividend_generate_top30.py

echo.
echo Stap 3: Dashboard openen in je browser...
start dividend_screener_dashboard.html
start dividend_top30_portfolio.html

echo.
echo Klaar!
goto end

:error
echo.
echo FOUT: Het script is mislukt. Controleer de foutmelding hierboven.

:end
pause
