import pandas as pd
import re
from datetime import datetime

def parse_country(name, category):
    """Bepaalt het land of de regio op basis van de naam en categorie."""
    name_lower = str(name).lower()
    if 'taiwan' in name_lower: return 'Taiwan'
    if 'poland' in name_lower: return 'Polen'
    if 'austria' in name_lower or 'atx' in name_lower.split(): return 'Oostenrijk'
    if 'india' in name_lower: return 'India'
    if 'china' in name_lower: return 'China'
    if 'japan' in name_lower: return 'Japan'
    if 'uk ' in name_lower or 'united kingdom' in name_lower or 'ftse 100' in name_lower: return 'Verenigd Koninkrijk'
    if 'germany' in name_lower or 'dax' in name_lower.split(): return 'Duitsland'
    if 'us ' in name_lower or 'u.s.' in name_lower or 'usa' in name_lower or 's&p 500' in name_lower or 'nasdaq' in name_lower or category == 'Region: US': return 'Verenigde Staten'
    if 'europe' in name_lower or 'euro stoxx' in name_lower: return 'Europa'
    if 'em ' in name_lower or 'emerging markets' in name_lower or 'emerging' in name_lower: return 'Emerging Markets'
    return 'Wereldwijd'

def parse_sector(name, category):
    """Bepaalt de sector of het thema op basis van de naam."""
    name_lower = str(name).lower()
    if 'goldman' in name_lower: return 'Brede Markt'
    if 'cybersecurity' in name_lower or 'cyber security' in name_lower: return 'Cybersecurity'
    if 'genomic' in name_lower or 'gn0m' in str(name).lower(): return 'Genomics'
    if 'biotech' in name_lower or 'biorevolution' in name_lower: return 'Biotech'
    if 'health' in name_lower: return 'Healthcare'
    if 'memory chips' in name_lower or 'semiconductor' in name_lower: return 'Semiconductors'
    if 'artificial intelligence' in name_lower or ' ai ' in name_lower: return 'AI / Robotica'
    if 'technology' in name_lower or 'tech' in name_lower: return 'Technologie'
    if 'value' in name_lower: return 'Value Factor'
    if 'growth' in name_lower: return 'Growth Factor'
    if 'dividend' in name_lower: return 'Dividend'
    if 'financial' in name_lower or 'banks' in name_lower: return 'Financiële sector'
    if 'industrial' in name_lower: return 'Industrie'
    if 'materials' in name_lower or 'mining' in name_lower or 'copper' in name_lower: return 'Basismetalen'
    if 'communication' in name_lower: return 'Communicatie'
    if 'esg' in name_lower or 'sri' in name_lower: return 'ESG / Duurzaam'
    return 'Brede Markt'

def genereer_etf_selectie(csv_pad='momentum_screener_result_final.csv', output_html='top30_portfolio.html'):
    try:
        df = pd.read_csv(csv_pad, sep='|')
    except FileNotFoundError:
        print(f"Fout: Kan {csv_pad} niet vinden.")
        return

    # Zorg voor unieke tickers
    df = df.drop_duplicates(subset=['yf_ticker'], keep='first')

    # Filter ETF's eruit die onder de 50MA zitten (Action == 'S')
    df = df[df['Action'] != 'S']
    # Bepaal custom velden
    df['Land_Regio'] = df.apply(lambda row: parse_country(row['name'], row['Category']), axis=1)
    df['Sector'] = df.apply(lambda row: parse_sector(row['name'], row['Category']), axis=1)
    df['Is_Acc'] = df['reinvest'].str.contains('Acc', case=False, na=False) | df['name'].str.contains('Acc', case=False, na=False)

    def pick_etfs(require_acc=False, huidige_selectie=None, landen_teller=None, sector_teller=None):
        if huidige_selectie is None: huidige_selectie = []
        if landen_teller is None: landen_teller = {}
        if sector_teller is None: sector_teller = {}
        
        selectie = list(huidige_selectie)
        l_teller = dict(landen_teller)
        s_teller = dict(sector_teller)
        
        for index, row in df.iterrows():
            if len(selectie) >= 30:
                break
                
            ticker = row['yf_ticker']
            if any(t['yf_ticker'] == ticker for t in selectie):
                continue
                
            if require_acc and not row['Is_Acc']:
                continue
                
            land = row['Land_Regio']
            sector = row['Sector']
            
            is_regio = land in ['Wereldwijd', 'Europa', 'Emerging Markets']
            if not is_regio and l_teller.get(land, 0) >= 1:
                continue
                
            if s_teller.get(sector, 0) >= 2:
                continue
                
            selectie.append(row)
            l_teller[land] = l_teller.get(land, 0) + 1
            s_teller[sector] = s_teller.get(sector, 0) + 1
            
        return selectie, l_teller, s_teller

    # Eerst ACC
    gekozen_etfs, l_counts, s_counts = pick_etfs(require_acc=True)
    # Vul aan met Distr
    if len(gekozen_etfs) < 30:
        gekozen_etfs, _, _ = pick_etfs(require_acc=False, huidige_selectie=gekozen_etfs, landen_teller=l_counts, sector_teller=s_counts)

    df_definitief = pd.DataFrame(gekozen_etfs).sort_values('Rank all')
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # HTML Genereren
    table_rows = ""
    for idx, row in df_definitief.iterrows():
        acc_class = "acc-badge" if row['Is_Acc'] else "dist-badge"
        acc_text = "Acc" if row['Is_Acc'] else "Dist"
        
        # Z-score check voor de groene/rode rij op basis van Action
        tr_class = ""
        action = str(row.get('Action', 'N')).strip()
        if action == 'S':
            tr_class = ' class="under-50ma"'
        elif action == 'B':
            tr_class = ' class="near-20ma"'
            
        table_rows += f"""
        <tr{tr_class}>
            <td><strong>{action}</strong></td>
            <td class="rank-cell">#{int(row['Rank all'])}</td>
            <td><strong>{row['yf_ticker']}</strong></td>
            <td>{row['name']}</td>
            <td>{row['Land_Regio']}</td>
            <td>{row['Sector']}</td>
            <td><span class="badge {acc_class}">{acc_text}</span></td>
            <td>{row['Total score']}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top 30 Momentum Portfolio</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#127919;</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --surface-color: #1e293b;
            --surface-hover: #334155;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-color: #3b82f6;
            --positive: #10b981;
            --warning: #f59e0b;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            padding: 2rem;
        }}

        header {{
            margin-bottom: 2rem;
            text-align: center;
        }}

        h1 {{
            font-size: 2.25rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .info-cards {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 2rem;
        }}
        
        .card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
            border-radius: 0.75rem;
            text-align: center;
        }}
        
        .card-val {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        .card-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        }}

        .table-container {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            overflow: auto;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }}

        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        thead {{ background: rgba(30, 41, 59, 0.9); border-bottom: 2px solid var(--border-color); }}
        th {{ padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.05em; }}
        
        tbody tr {{ border-bottom: 1px solid var(--border-color); transition: background-color 0.15s; }}
        tbody tr:hover {{ background-color: var(--surface-hover); }}
        td {{ padding: 1rem; font-size: 0.875rem; vertical-align: middle; }}
        
        /* Rijen waarbij de koers binnen ±0.5 Z-score van de 20MA zit (pullback/consolidatie zone) */
        tbody tr.near-20ma {{ background-color: rgba(16, 185, 129, 0.07); }}
        tbody tr.near-20ma:hover {{ background-color: rgba(16, 185, 129, 0.14); }}
        tbody tr.near-20ma td {{ color: #6ee7b7; }}
        tbody tr.near-20ma td.rank-cell {{ color: #34d399; }}
        
        /* Rijen waarbij koers onder de 50MA zit (verkoop/zwak) */
        tbody tr.under-50ma {{ background-color: rgba(239, 68, 68, 0.07); }}
        tbody tr.under-50ma:hover {{ background-color: rgba(239, 68, 68, 0.14); }}
        tbody tr.under-50ma td {{ color: #fca5a5; }}
        tbody tr.under-50ma td.rank-cell {{ color: #f87171; }}
        
        .rank-cell {{
            font-weight: 700;
            color: var(--positive);
        }}

        .badge {{
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        .acc-badge {{
            background: rgba(16, 185, 129, 0.1);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}
        
        .dist-badge {{
            background: rgba(245, 158, 11, 0.1);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.2);
        }}

    </style>
</head>
<body>
    <header>
        <h1>Top 30 Momentum Portfolio</h1>
        <div class="subtitle">Equal Weight Strategie • Gegenereerd op {current_time}</div>
    </header>
    
    <div class="info-cards">
        <div class="card">
            <div class="card-val">30</div>
            <div class="card-label">Posities</div>
        </div>
        <div class="card">
            <div class="card-val">3.3%</div>
            <div class="card-label">Weging per positie</div>
        </div>
        <div class="card">
            <div class="card-val">{len([e for e in gekozen_etfs if e['Is_Acc']])}</div>
            <div class="card-label">Accumulerend</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Actie</th>
                    <th>Overall Rank</th>
                    <th>Ticker</th>
                    <th>Naam ETF</th>
                    <th>Land / Regio</th>
                    <th>Sector / Thema</th>
                    <th>Type</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Top 30 HTML dashboard succesvol aangemaakt: {output_html}")

if __name__ == "__main__":
    genereer_etf_selectie()
