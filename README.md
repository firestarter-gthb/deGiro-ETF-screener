# DEGIRO ETF Momentum Screener

Dit project bevat een geautomatiseerde momentum screener voor ETF's die verhandelbaar zijn op DEGIRO. Het haalt de actuele ETF data en koersen op via Yahoo Finance, berekent diverse momentum- en performance-indicatoren, en genereert een interactief HTML-dashboard om de resultaten te analyseren.

## Features

- **Data Extractie:** Haalt een brede lijst aan DEGIRO ETF's op (o.a. via ISIN en Yahoo Tickers).
- **Rate Limit Handeling:** Maakt gebruik van chunking en sessies om IP-bans (HTTP 429) van Yahoo Finance te voorkomen.
- **Momentum Scoring:** Berekent uitgebreide statistieken zoals:
  - Total Score (gebaseerd op wegingen van rendementen)
  - YTD Performance
  - Afstand tot het 20- en 200-daags voortschrijdend gemiddelde (Moving Average)
  - Korte en lange termijn rankings
- **Automatische Categorisatie:** Gebruikt regex om ETF's in logische sectoren (bijv. Technology, Healthcare, World, Europe) in te delen.
- **Dividend Beleid:** Herkent automatisch of een ETF Accumulerend of Distribuerend is (Acc/Distr).
- **Interactief Dashboard:** Genereert een lokaal HTML-bestand (`momentum_screener_dashboard.html`) met:
  - Multi-select checkbox filtering per Categorie.
  - Vrije tekst search voor naam of ISIN.
  - Dropdown filtering voor valuta en dividendbeleid.
  - Sortering per kolom.
  - Reset filters functionaliteit.

## Bestanden

- `momentum_screener.py`: Het hoofdscript. Verzamelt data, berekent de scores, filtert illiquide of verouderde ETF's eruit, en slaat dit op in een CSV.
- `generate_html.py`: Converteert de gegenereerde CSV-data naar een rijk interactief HTML dashboard zonder externe afhankelijkheden (behalve lettertypes).
- `degiro_etfs.csv`: De brondata met de initiële ETF-mapping voor DEGIRO.
- `momentum_screener_dashboard.html`: Het resulterende dashboard (wordt lokaal aangemaakt na een run).

## Gebruik

1. Installeer de benodigde Python packages (zoals `pandas` en `yfinance`):
   ```bash
   pip install pandas yfinance
   ```

2. Draai de momentum screener om de nieuwste koersen op te halen (dit kan enkele minuten duren vanwege API-limieten):
   ```bash
   python momentum_screener.py
   ```

3. Het HTML dashboard wordt automatisch gegenereerd. Open `momentum_screener_dashboard.html` in je favoriete webbrowser om de ETF's te filteren en sorteren.
