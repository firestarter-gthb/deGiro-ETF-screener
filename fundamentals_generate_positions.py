import pandas as pd
import numpy as np
from datetime import datetime
import os

def genereer_fundamentals_posities_dashboard(pos_csv='fundamentals_positions.csv', fun_csv='fundamentals_screener_result_final.csv', output_html='fundamentals_huidige_posities.html'):
    if not os.path.exists(pos_csv):
        print(f"Fout: Kan {pos_csv} niet vinden.")
        return
    if not os.path.exists(fun_csv):
        print(f"Fout: Kan {fun_csv} niet vinden.")
        return

    df_pos = pd.read_csv(pos_csv, sep='|')
    df_fun = pd.read_csv(fun_csv, sep='|')
    
    # Merge de data
    df_pos['isin'] = df_pos['ISIN'].astype(str).str.strip()
    df_fun['isin'] = df_fun['isin'].astype(str).str.strip()
    
    df_fun_unique = df_fun.drop_duplicates(subset=['isin'])
    df_merged = pd.merge(df_pos, df_fun_unique, on='isin', how='left')

    # Fallback: als ISIN niet matcht (bijv. door Degiro/Yahoo ticker dubbelingen), match op Symbool
    for idx, row in df_merged.iterrows():
        if pd.isna(row.get('Rank')):
            sym = str(row['Symbool']).strip()
            fallback = df_fun[df_fun['yf_ticker'].str.startswith(f"{sym}.")].head(1)
            if not fallback.empty:
                for col in df_fun.columns:
                    if col != 'isin': 
                        df_merged.at[idx, col] = fallback.iloc[0][col]

    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # HTML Genereren
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Mijn Huidige Fundamentals & Risico Posities</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f6f9; color: #333; }}
        h1 {{ color: #2c3e50; }}
        .header-info {{ margin-bottom: 20px; color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 14px; margin-bottom: 30px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #8e44ad; color: white; cursor: pointer; }}
        th:hover {{ background: #732d91; }}
        tr:hover {{ background: #f1f1f1; }}
        .volatility-high {{ color: #e74c3c; font-weight: bold; }}
        .volatility-low {{ color: #27ae60; font-weight: bold; }}
        .drawdown-deep {{ color: #c0392b; }}
        .drawdown-safe {{ color: #2980b9; }}
        .sharpe-good {{ color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>💼 Mijn Huidige Fundamentals & Risico Posities</h1>
    <div class="header-info">
        <p>Live risico metrics en fundamenten van je huidige portefeuille.</p>
        <p><em>Laatste update: {current_time}</em></p>
    </div>
    
    <table id="positionsTable">
        <thead>
            <tr>
                <th>Start Datum</th>
                <th>Symbool</th>
                <th>Naam ETF</th>
                <th>GICS Sector L1</th>
                <th>GICS Sector L2</th>
                <th>Huidige Rank</th>
                <th>Aantal</th>
                <th>Aankoopkoers</th>
                <th>Huidige Prijs</th>
                <th>Rendement (%)</th>
                <th>Sharpe Ratio</th>
                <th>Max Drawdown (%)</th>
                <th>Volatiliteit (%)</th>
            </tr>
        </thead>
        <tbody>
"""

    totale_waarde = 0
    totale_inleg = 0

    for idx, row in df_merged.iterrows():
        aantal = row.get('Aantal', np.nan)
        aankoop = row.get('Aankoopkoers', np.nan)
        huidig = row.get('Price', np.nan)
        
        waarde = 0
        inleg = 0
        rendement = 0
        if not pd.isna(aantal) and not pd.isna(aankoop) and not pd.isna(huidig):
            waarde = aantal * huidig
            inleg = aantal * aankoop
            if inleg > 0:
                rendement = ((waarde - inleg) / inleg) * 100
            totale_waarde += waarde
            totale_inleg += inleg
            
        rank_val = f"#{int(row['Rank'])}" if not pd.isna(row.get('Rank')) else "-"
        vol = row.get('Volatiliteit (%)', np.nan)
        dd = row.get('Max Drawdown (%)', np.nan)
        sharpe = row.get('Sharpe Ratio', np.nan)
        
        vol_class = "" 
        dd_class = ""
        sharpe_class = ""
        
        if not pd.isna(vol):
            vol_class = "volatility-low" if vol < 15 else ("volatility-high" if vol > 25 else "")
        if not pd.isna(dd):
            dd_class = "drawdown-safe" if dd > -10 else ("drawdown-deep" if dd < -25 else "")
        if not pd.isna(sharpe):
            sharpe_class = "sharpe-good" if sharpe > 1.5 else ""

        naam = row.get('name', 'Onbekend')
        
        huidig_str = f"€{huidig:.2f}" if not pd.isna(huidig) else "-"
        aankoop_str = f"€{aankoop:.2f}" if not pd.isna(aankoop) else "-"
        rend_color = "green" if rendement >= 0 else "red"
        
        vol_str = f"{vol:.2f}%" if not pd.isna(vol) else "-"
        dd_str = f"{dd:.2f}%" if not pd.isna(dd) else "-"
        sharpe_str = f"{sharpe:.2f}" if not pd.isna(sharpe) else "-"

        html += f"""            <tr>
                <td>{row['Start'] if not pd.isna(row.get('Start')) else '-'}</td>
                <td><strong>{row.get('Symbool', '-')}</strong></td>
                <td>{naam}</td>
                <td>{row.get('GICS Sector L1', '-')}</td>
                <td>{row.get('GICS Sector L2', '-')}</td>
                <td>{rank_val}</td>
                <td>{aantal if not pd.isna(aantal) else '-'}</td>
                <td>{aankoop_str}</td>
                <td>{huidig_str}</td>
                <td style="color: {rend_color}; font-weight: bold;">{rendement:.2f}%</td>
                <td class="{sharpe_class}">{sharpe_str}</td>
                <td class="{dd_class}">{dd_str}</td>
                <td class="{vol_class}">{vol_str}</td>
            </tr>
"""

    totaal_rendement = 0
    if totale_inleg > 0:
        totaal_rendement = ((totale_waarde - totale_inleg) / totale_inleg) * 100

    html += f"""        </tbody>
    </table>
    
    <h2>💰 Portefeuille Overzicht</h2>
    <table style="width: 50%;">
        <tr><td><strong>Totale Inleg:</strong></td><td>€{totale_inleg:.2f}</td></tr>
        <tr><td><strong>Huidige Waarde:</strong></td><td>€{totale_waarde:.2f}</td></tr>
        <tr><td><strong>Totaal Rendement:</strong></td><td style="color: {'green' if totaal_rendement >= 0 else 'red'}; font-weight: bold;">{totaal_rendement:.2f}%</td></tr>
    </table>
    
    <script>
        const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
        const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
            v1 !== '' && v2 !== '' && !isNaN(v1.replace(/[^0-9.-]+/g,"")) && !isNaN(v2.replace(/[^0-9.-]+/g,"")) ? 
            v1.replace(/[^0-9.-]+/g,"") - v2.replace(/[^0-9.-]+/g,"") : v1.toString().localeCompare(v2)
            )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

        document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {{
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            Array.from(tbody.querySelectorAll('tr'))
                .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                .forEach(tr => tbody.appendChild(tr) );
        }})));
    </script>
</body>
</html>"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Huidige posities dashboard gegenereerd: {output_html}")

if __name__ == "__main__":
    genereer_fundamentals_posities_dashboard()
