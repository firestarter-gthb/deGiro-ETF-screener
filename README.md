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

## Installatie / Vereisten

Om deze applicatie (de screener en de dashboards) op je pc te kunnen draaien, heb je het volgende nodig:

1. **Python 3.8 of nieuwer**: Zorg dat Python geïnstalleerd is op je computer. (Te downloaden via [python.org](https://www.python.org/downloads/)).
2. **Een webbrowser**: (Google Chrome, Edge, Safari of Firefox) om de gegenereerde dashboards (`.html`) in te openen.
3. **Python Packages**: De scripts maken gebruik van een aantal externe libraries.

Installeer alle benodigde Python packages in één keer via het meegeleverde `requirements.txt` bestand. Open je terminal of command prompt in de map van dit project en run:

```bash
pip install -r requirements.txt
```

*(Mocht je ze handmatig willen installeren, de benodigde pakketten zijn o.a.: `pandas`, `numpy`, `yfinance`, `requests`, en `degiro-connector`).*

## Gebruik

1. **Nieuwe data ophalen & Screener draaien:** 
   Voer het `run_screener.bat` script uit, óf draai handmatig:
   ```bash
   python momentum_screener.py
   ```
   *Let op: Dit verzamelt de actuele koersen van honderden ETF's en kan enkele minuten duren vanwege API-limieten van Yahoo Finance.*

2. **Dashboards bekijken:**
   - **Hoofd Screener:** Open `momentum_screener_dashboard.html` in je webbrowser voor de complete lijst en filters.
   - **Top 30 Portfolio:** Open `top30_portfolio.html` voor de samengestelde portfolio van de beste ETF's.
   - **Huidige Posities:** Vul je eigen ETF's en aankoopkoersen in binnen `positions.csv` en draai `python generate_positions.py`. Open vervolgens `huidige_posities.html` om de live voortgang van je portefeuille te tracken.
