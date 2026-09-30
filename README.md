# DEGIRO ETF Analyse Suite (Momentum, Dividend, Fundamentals)

Dit project bevat geautomatiseerde screeners voor ETF's die verhandelbaar zijn op DEGIRO. Het haalt de actuele ETF data en koersen op via Yahoo Finance en genereert drie krachtige interactieve HTML-dashboards om de resultaten te analyseren op basis van: Momentum, Dividend, en Fundamenteel Risico.

## 🚀 De Drie Screeners

1. **Momentum Screener (`run_momentum_screener.bat`)**
   - Vindt de ETF's die momenteel de sterkste stijgende trends laten zien.
   - Berekent 1M, 3M, 6M rendementen, afstand tot 20/200 Moving Average, en een gewogen Total Score.

2. **Dividend Screener (`run_dividend_screener.bat`)**
   - Specifiek gericht op *Distribuerende* ETF's. Vindt de hoogste en meest stabiele dividendrendementen.
   - Filtert automatisch gevaarlijke "Value Traps" (dalende koersen) en extreem risicovolle "Covered Call" constructies eruit.

3. **Fundamentals & Risico Screener (`run_fundamentals_screener.bat`)**
   - Kijkt puur naar het wiskundige risico over het afgelopen jaar en de fundamenten.
   - Berekent harde metrics: *Volatiliteit* (schommelingen), *Sharpe Ratio* (rendement vs risico), en *Maximum Drawdown* (grootste historische daling).
   - Vult aan met *P/E Ratio* en *Assets* voor de ETF's waar dit beschikbaar is op Yahoo Finance.

## 🛠 Algemene Features

- **Rate Limit Handeling:** Maakt gebruik van caching en delays om IP-bans van Yahoo Finance te voorkomen.
- **Top 30 Portfolios:** Elke screener genereert naast de volledige lijst ook automatisch een actuele Top 30 van de absolute winnaars binnen de categorie.
- **Huidige Posities Tracken:** Vul je eigen ETF's en aankoopkoersen in binnen de betreffende `_positions.csv` bestanden (bijv. `momentum_positions.csv`). Het script koppelt deze aan de laatste data zodat je live kunt bijhouden hoe jouw portfolio presteert!
- **Interactieve Dashboards:** Alle resultaten worden lokaal opgeslagen als `.html` bestanden. Deze bevatten krachtige zoekvelden, multi-select filters en automatische kleurencodering, en werken direct in je browser.

## 📂 Hoe te Gebruiken

1. **Data updaten & Screenen**
   Draai simpelweg een van de `.bat` bestanden om de volledige analyse uit te voeren:
   - `run_momentum_screener.bat`
   - `run_dividend_screener.bat`
   - `run_fundamentals_screener.bat`
   *(Let op: Het ophalen van koershistorie voor ~1600 ETF's duurt per screener zo'n 10-15 minuten!)*

2. **Resultaten bekijken**
   Na afloop opent de software automatisch twee schermen in je browser:
   - Het **Hoofddashboard** (alle ETF's met filters)
   - De **Top 30 Portfolio** (de winnaars)

3. **Mijn Huidige Posities bekijken**
   Vul de CSV-bestanden (zoals `fundamentals_positions.csv`) met de ETF's die je daadwerkelijk bezit. Draai vervolgens het bijbehorende script, bijvoorbeeld:
   ```bash
   python fundamentals_generate_positions.py
   ```
   Open het nieuw gemaakte `.html` bestand om je persoonlijke statistieken te bekijken.

## ⚙️ Installatie / Vereisten

Om de screeners te kunnen draaien heb je het volgende nodig:

1. **Python 3.8 of nieuwer**: [Download Python](https://www.python.org/downloads/).
2. **Een webbrowser**: (Google Chrome, Edge, Safari of Firefox) om de dashboards te bekijken.
3. **Python Packages**: Installeer de vereiste pakketten in één keer door het volgende commando uit te voeren in de projectmap:
   ```bash
   pip install -r requirements.txt
   ```
