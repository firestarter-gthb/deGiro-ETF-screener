import pandas as pd
from datetime import datetime
import os

def genereer_posities_dashboard(pos_csv='positions.csv', mom_csv='momentum_screener_result_final.csv', output_html='huidige_posities.html'):
    # Lees bestanden
    try:
        df_pos = pd.read_csv(pos_csv, sep='|')
        df_pos.columns = [c.strip() for c in df_pos.columns]
    except FileNotFoundError:
        print(f"Fout: {pos_csv} niet gevonden.")
        return

    try:
        df_mom = pd.read_csv(mom_csv, sep='|')
    except FileNotFoundError:
        print(f"Fout: {mom_csv} niet gevonden.")
        return

    # Merge de data
    # pos_csv heeft 'ISIN', mom_csv heeft 'isin'
    df_pos['isin'] = df_pos['ISIN'].astype(str).str.strip()
    df_mom['isin'] = df_mom['isin'].astype(str).str.strip()
    
    # Verwijder duplicaten in de momentum data om dubbele rijen te voorkomen
    df_mom = df_mom.drop_duplicates(subset=['isin'])
    
    df_merged = pd.merge(df_pos, df_mom, on='isin', how='left')

    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # HTML Genereren
    table_rows = ""
    for idx, row in df_merged.iterrows():
        # Fallback voor ontbrekende momentum data
        rank = row['Rank all'] if pd.notnull(row.get('Rank all')) else '-'
        
        action = row.get('Action')
        action = str(action).strip() if pd.notnull(action) else '-'
        
        score = row['Total score'] if pd.notnull(row.get('Total score')) else '-'
        name = row['name'] if pd.notnull(row.get('name')) else row['Symbool']
        
        category = row.get('Category')
        category = str(category).strip() if pd.notnull(category) else '-'
        
        # Z-score check voor de groene/rode rij op basis van Action
        tr_class = ""
        if action == 'S':
            tr_class = ' class="under-50ma"'
        elif action == 'B':
            tr_class = ' class="near-20ma"'
            
        aantal_raw = row.get('Aantal')
        try:
            aantal = float(aantal_raw) if pd.notnull(aantal_raw) else 0.0
        except ValueError:
            aantal = 0.0
            
        aankoopkoers_raw = row.get('Aankoopkoers')
        try:
            aankoopkoers = float(aankoopkoers_raw) if pd.notnull(aankoopkoers_raw) else 0.0
        except ValueError:
            aankoopkoers = 0.0
            
        current_price_raw = row.get('Current price')
        try:
            if isinstance(current_price_raw, str):
                current_price = float(current_price_raw.replace(',', '.'))
            else:
                current_price = float(current_price_raw) if pd.notnull(current_price_raw) else 0.0
        except ValueError:
            current_price = 0.0

        start_raw = row.get('Start')
        days_open = None
        if pd.notnull(start_raw):
            start_str = str(int(start_raw)) if isinstance(start_raw, float) else str(start_raw).strip()
            # Try to format YYYYMMDD to DD-MM-YYYY
            if len(start_str) == 8 and start_str.isdigit():
                start_formatted = f"{start_str[6:8]}-{start_str[4:6]}-{start_str[0:4]}"
                try:
                    start_date = datetime.strptime(start_str, "%Y%m%d")
                    days_open = (datetime.now() - start_date).days
                except ValueError:
                    pass
            else:
                start_formatted = start_str
        else:
            start_formatted = '-'
            
        datum_huidig = datetime.now().strftime("%d-%m-%Y")

        waarde_aankoop = aantal * aankoopkoers
        waarde_nu = aantal * current_price

        # Als de positie minder of gelijk aan 2 dagen open is, rapporteer 0% rendement
        # en stel huidige waarde gelijk aan aankoopwaarde (behalve als aankoopwaarde 0 is).
        if days_open is not None and days_open <= 2 and waarde_aankoop > 0:
            waarde_nu = waarde_aankoop
            rendement_pct = 0.0
        else:
            if waarde_aankoop > 0:
                rendement_pct = ((waarde_nu - waarde_aankoop) / waarde_aankoop) * 100
            else:
                rendement_pct = 0.0

        rendement_class = "rank-cell" if rendement_pct >= 0 else "under-50ma" 
        # Actually, will just style it with custom color
        rendement_color = "var(--text-secondary)" if rendement_pct == 0.0 else ("var(--positive)" if rendement_pct > 0 else "var(--negative)")
        rendement_str = f"<span style='color: {rendement_color}; font-weight: 600;'>{rendement_pct:+.2f}%</span>" if waarde_aankoop > 0 else "-"
        
        waarde_aankoop_str = f"€ {waarde_aankoop:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if waarde_aankoop > 0 else "-"
        waarde_nu_str = f"€ {waarde_nu:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if waarde_nu > 0 else "-"
        
        aantal_str = str(aantal_raw).strip() if pd.notnull(aantal_raw) else '-'
        
        table_rows += f"""
        <tr{tr_class}>
            <td><strong>{action}</strong></td>
            <td>{aantal_str}</td>
            <td class="rank-cell">#{rank}</td>
            <td><strong>{row['Symbool']}</strong></td>
            <td>{name}</td>
            <td>{category}</td>
            <td>{start_formatted}</td>
            <td>{waarde_aankoop_str}</td>
            <td>{datum_huidig}</td>
            <td>{waarde_nu_str}</td>
            <td>{rendement_str}</td>
            <td>{score}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Huidige Posities</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#128188;</text></svg>">
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
            --positive: #10b981;
            --negative: #ef4444;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        header {{
            text-align: center;
            margin-bottom: 2rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            font-weight: 400;
        }}

        .info-cards {{
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            justify-content: center;
            width: 100%;
            max-width: 1600px;
        }}

        .card {{
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            border-radius: 0.75rem;
            flex: 1;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}

        .card-val {{
            font-size: 2rem;
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
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }}

        table {{ width: 100%; border-collapse: collapse; text-align: left; }}
        thead {{ background: rgba(30, 41, 59, 0.9); border-bottom: 2px solid var(--border-color); }}
        th {{ padding: 1rem; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.05em; white-space: nowrap; }}
        
        tbody tr {{ border-bottom: 1px solid var(--border-color); transition: background-color 0.15s; }}
        tbody tr:hover {{ background-color: var(--surface-hover); }}
        td {{ padding: 1rem; font-size: 0.875rem; vertical-align: middle; white-space: nowrap; }}
        
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

    </style>
</head>
<body>
    <header>
        <h1>Huidige Posities</h1>
        <div class="subtitle">Analyse van je portefeuille • Gegenereerd op {current_time}</div>
    </header>
    
    <div class="info-cards">
        <div class="card">
            <div class="card-val">{len(df_merged)}</div>
            <div class="card-label">Aantal Posities</div>
        </div>
        <div class="card">
            <div class="card-val">{len(df_merged[df_merged['Action'] == 'S'])}</div>
            <div class="card-label">Rood (S)</div>
        </div>
        <div class="card">
            <div class="card-val">{len(df_merged[df_merged['Action'] == 'B'])}</div>
            <div class="card-label">Groen (B)</div>
        </div>
    </div>

    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Actie</th>
                    <th>Aantal</th>
                    <th>Overall Rank</th>
                    <th>Symbool</th>
                    <th>Naam ETF</th>
                    <th>Categorie</th>
                    <th>Openingsdatum</th>
                    <th>Waarde bij aankoop</th>
                    <th>Datum huidig</th>
                    <th>Huidige waarde</th>
                    <th>Resultaat (%)</th>
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
    print(f"Huidige posities dashboard succesvol aangemaakt: {output_html}")

if __name__ == "__main__":
    genereer_posities_dashboard()
