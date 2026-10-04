from ds_layout import apply_theme
import pandas as pd
import re
from datetime import datetime

def parse_country(name):
    name_lower = str(name).lower()
    if 'taiwan' in name_lower: return 'Taiwan'
    if 'poland' in name_lower: return 'Polen'
    if 'austria' in name_lower or 'atx' in name_lower.split(): return 'Oostenrijk'
    if 'india' in name_lower: return 'India'
    if 'china' in name_lower: return 'China'
    if 'japan' in name_lower: return 'Japan'
    if 'uk ' in name_lower or 'united kingdom' in name_lower or 'ftse 100' in name_lower: return 'Verenigd Koninkrijk'
    if 'germany' in name_lower or 'dax' in name_lower.split(): return 'Duitsland'
    if 'us ' in name_lower or 'u.s.' in name_lower or 'usa' in name_lower or 's&p 500' in name_lower or 'nasdaq' in name_lower: return 'Verenigde Staten'
    if 'europe' in name_lower or 'euro stoxx' in name_lower: return 'Europa'
    if 'em ' in name_lower or 'emerging markets' in name_lower or 'emerging' in name_lower: return 'Emerging Markets'
    return 'Wereldwijd'

def parse_sector(name):
    name_lower = str(name).lower()
    if 'real estate' in name_lower or 'property' in name_lower: return 'Vastgoed'
    if 'utility' in name_lower or 'utilities' in name_lower: return 'Nutsvoorzieningen'
    if 'financial' in name_lower or 'banks' in name_lower: return 'Financiële sector'
    if 'energy' in name_lower or 'oil' in name_lower: return 'Energie'
    if 'health' in name_lower or 'healthcare' in name_lower: return 'Healthcare'
    if 'tech' in name_lower or 'technology' in name_lower: return 'Technologie'
    if 'infrastructure' in name_lower: return 'Infrastructuur'
    if 'consumer' in name_lower: return 'Consumentengoederen'
    return 'Brede Markt'

def genereer_dividend_top30(csv_pad='dividend_screener_result_final.csv', output_html='dividend_top30_portfolio.html'):
    try:
        df = pd.read_csv(csv_pad, sep='|')
    except FileNotFoundError:
        print(f"Fout: Kan {csv_pad} niet vinden.")
        return

    # 1. Filter Covered Calls en Value Traps
    gevaarlijke_woorden = ['covered call', 'buywrite', 'premium', 'high dividend yield', 'yield plus']
    df = df[~df['name'].str.lower().apply(lambda x: any(w in x for w in gevaarlijke_woorden))]

    # 2. Harde eisen voor dividend kwaliteit
    # Yield niet té hoog (Value Trap protectie) en niet te laag
    df = df[(df['Yield (%)'] >= 2.0) & (df['Yield (%)'] <= 8.0)]
    
    # Groei moet enigszins oké zijn (mag onbekend zijn, maar niet zwaar negatief)
    df = df[(df['Growth 3y (%)'] >= -5.0) | (df['Growth 3y (%)'].isna())]
    
    # ETF moet consistent betalen (minimaal 2x per jaar)
    df = df[df['Divs TTM'] >= 2]

    # Voeg Regio en Sector toe
    df['Land_Regio'] = df['name'].apply(parse_country)
    df['Sector'] = df['name'].apply(parse_sector)

    # Selectie logica met spreiding
    selectie = []
    landen_teller = {}
    sector_teller = {}

    for index, row in df.iterrows():
        if len(selectie) >= 30:
            break
            
        land = row['Land_Regio']
        sector = row['Sector']
        
        is_regio = land in ['Wereldwijd', 'Europa', 'Emerging Markets']
        if not is_regio and landen_teller.get(land, 0) >= 2:
            continue
            
        if sector != 'Brede Markt' and sector_teller.get(sector, 0) >= 3:
            continue

        selectie.append(row)
        landen_teller[land] = landen_teller.get(land, 0) + 1
        sector_teller[sector] = sector_teller.get(sector, 0) + 1

    if not selectie:
        print("Geen ETF's voldeden aan de strenge dividend criteria.")
        return

    df_top30 = pd.DataFrame(selectie)

    # HTML Genereren (simpele versie gebaseerd op momentum)
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    table_rows = ""
    for i, row in df_top30.iterrows():
        table_rows += f"""<tr>
            <td>{row['yf_ticker']}</td>
            <td>{row['name']}</td>
            <td>{row['Land_Regio']}</td>
            <td>{row['Sector']}</td>
            <td>{row.get('GICS Sector L1', '-')}</td>
            <td>{row.get('GICS Sector L2', '-')}</td>
            <td>{row['Yield (%)']:.2f}%</td>
            <td>{row['Growth 3y (%)'] if not pd.isna(row['Growth 3y (%)']) else 'N/A'}</td>
            <td>{row['Score']:.2f}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Top 30 Dividend Portfolio</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f9f9f9; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #2c3e50; color: white; }}
        tr:hover {{ background: #f1f1f1; }}
    </style>
</head>
<body>
    <h1>🏆 Top 30 Dividend Portfolio</h1>
    <p>Gefilterd op kwaliteit, gevaarlijke yields (Value Traps / Covered Calls) zijn weggelaten, met sectorspreiding.</p>
    <p><em>Laatste update: {current_time}</em></p>
    <table>
        <thead>
            <tr>
                <th>Ticker</th>
                <th>Naam ETF</th>
                <th>Land / Regio</th>
                <th>Sector</th>
                <th>GICS Sector L1</th>
                <th>GICS Sector L2</th>
                <th>Yield (%)</th>
                <th>Groei 3j (%)</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
</body>
</html>"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(apply_theme(html, 'dividend30'))
    print(f"Dividend Top 30 succesvol aangemaakt: {output_html}")

if __name__ == "__main__":
    genereer_dividend_top30()
